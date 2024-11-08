import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import re
import sys
from cryptography.fernet import Fernet
import datetime
from collections import Counter
from mutagen import File as MutagenFile
import time

def load_key():
    """Load the encryption key from a file or generate a new one."""
    key_file = 'key.key'
    if os.path.exists(key_file):
        with open(key_file, 'rb') as file:
            key = file.read()
    else:
        key = Fernet.generate_key()
        with open(key_file, 'wb') as file:
            file.write(key)
    return key

def save_credentials(client_id, client_secret):
    """Encrypt and save the Spotify credentials."""
    key = load_key()
    f = Fernet(key)
    credentials = f'{client_id}:{client_secret}'.encode()
    encrypted_credentials = f.encrypt(credentials)
    with open('credentials.enc', 'wb') as file:
        file.write(encrypted_credentials)

def load_credentials():
    """Load and decrypt the Spotify credentials."""
    key = load_key()
    f = Fernet(key)
    with open('credentials.enc', 'rb') as file:
        encrypted_credentials = file.read()
    decrypted_credentials = f.decrypt(encrypted_credentials).decode()
    client_id, client_secret = decrypted_credentials.split(':')
    return client_id, client_secret

def parse_m3u(file_path):
    """Parse an M3U playlist file and extract track information."""
    tracks = []
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('#EXTINF:'):
                info = line.split('#EXTINF:')[1]
                # Extract artist and title
                match = re.match(r'[\d-]+,(.*) - (.*)', info)
                if match:
                    artist = match.group(1).strip()
                    title = match.group(2).strip()
                else:
                    # Handle cases where the format is different
                    title_info = info.split(',', 1)[-1]
                    if ' - ' in title_info:
                        artist, title = title_info.split(' - ', 1)
                        artist = artist.strip()
                        title = title.strip()
                    else:
                        # If format is unknown, set artist and title as unknown
                        artist = 'unknown artist'
                        title = 'unknown title'

                # Check for unknown artist and title
                if artist.lower() == 'unknown artist' and title.lower() == 'unknown title':
                    # Try to use filename
                    i += 1  # Move to the next line which should be the file path
                    if i < len(lines):
                        file_line = lines[i].strip()
                        filename = os.path.basename(file_line)
                        # Remove file extension
                        filename_no_ext = os.path.splitext(filename)[0]
                        # Try to split filename into artist and title
                        if ' - ' in filename_no_ext:
                            artist, title = filename_no_ext.split(' - ', 1)
                        else:
                            title = filename_no_ext
                            artist = 'unknown artist'
                tracks.append({'artist': artist.strip(), 'title': title.strip()})
            i += 1
    return tracks

def parse_audio_file(file_path):
    """Extract artist and title from an audio file's metadata."""
    try:
        audio = MutagenFile(file_path, easy=True)
        if audio is None:
            print(f"Unsupported audio format: {file_path}")
            return None
        artist = audio.get('artist', ['unknown artist'])[0]
        title = audio.get('title', ['unknown title'])[0]
        return {'artist': artist.strip(), 'title': title.strip()}
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def parse_audio_folder(folder_path):
    """Recursively parse a folder to extract track information from audio files."""
    supported_extensions = ['.mp3', '.flac', '.wav', '.m4a', '.aac', '.ogg']
    tracks = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if os.path.splitext(file)[1].lower() in supported_extensions:
                file_path = os.path.join(root, file)
                track_info = parse_audio_file(file_path)
                if track_info:
                    tracks.append(track_info)
    return tracks

def search_track(sp, artist, title):
    """Search for a track on Spotify and return its ID."""
    query = f'artist:{artist} track:{title}'
    try:
        result = sp.search(q=query, type='track', limit=1)
        tracks = result['tracks']['items']
        if tracks:
            return tracks[0]['id']
        else:
            return None
    except spotipy.exceptions.SpotifyException as e:
        print(f"Error searching for track '{artist} - {title}': {e}")
        return None

def get_recommendations(sp, seed_tracks, additional_params):
    """
    Get track recommendations from Spotify based on seed tracks and additional parameters.
    Ensures that no more than 5 seed tracks are used per API call.
    """
    all_recommendations = []
    # Spotify allows a maximum of 5 seeds (tracks, artists, genres)
    # We'll batch seed_tracks into groups of 5
    max_seeds = 5
    seed_batches = [seed_tracks[i:i + max_seeds] for i in range(0, len(seed_tracks), max_seeds)]
    
    for batch in seed_batches:
        try:
            recommendations = sp.recommendations(seed_tracks=batch, limit=100, **additional_params)
            all_recommendations.extend(recommendations['tracks'])
            # To avoid hitting rate limits
            time.sleep(0.1)
        except spotipy.exceptions.SpotifyException as e:
            print(f"Error fetching recommendations with seeds {batch}: {e}")
            continue
    return all_recommendations

def create_playlist(sp, user_id, name, description=''):
    """Create a new Spotify playlist."""
    try:
        playlist = sp.user_playlist_create(user=user_id, name=name, public=False, description=description)
        return playlist['id']
    except spotipy.exceptions.SpotifyException as e:
        print(f"Error creating playlist '{name}': {e}")
        return None

def add_tracks_to_playlist(sp, playlist_id, track_ids):
    """Add tracks to a Spotify playlist in batches of 100."""
    try:
        for i in range(0, len(track_ids), 100):
            sp.playlist_add_items(playlist_id, track_ids[i:i+100])
            # To avoid hitting rate limits
            time.sleep(0.1)
    except spotipy.exceptions.SpotifyException as e:
        print(f"Error adding tracks to playlist: {e}")

def get_genres(sp, artist_ids):
    """Retrieve genres for a list of artist IDs."""
    genres = []
    # Batch the artist IDs
    for i in range(0, len(artist_ids), 50):
        batch_ids = artist_ids[i:i+50]
        try:
            artists = sp.artists(batch_ids)['artists']
            for artist in artists:
                genres.extend(artist['genres'])
            # To avoid hitting rate limits
            time.sleep(0.1)
        except spotipy.exceptions.SpotifyException as e:
            print(f"Error fetching genres for artists {batch_ids}: {e}")
            continue
    return genres

def get_input_tracks(input_path):
    """Determine the type of input and parse tracks accordingly."""
    if os.path.isfile(input_path):
        if input_path.lower().endswith('.m3u'):
            return parse_m3u(input_path)
        elif os.path.splitext(input_path)[1].lower() in ['.mp3', '.flac', '.wav', '.m4a', '.aac', '.ogg']:
            track = parse_audio_file(input_path)
            return [track] if track else []
        else:
            print("Unsupported file type. Please provide an M3U playlist or a supported audio file.")
            return []
    elif os.path.isdir(input_path):
        return parse_audio_folder(input_path)
    else:
        print("Invalid input path. Please provide a valid file or directory.")
        return []

def filter_tracks_by_release_year(sp, tracks, min_year=None, max_year=None):
    """
    Filter tracks based on their album's release year.
    Since the Spotify Recommendations API doesn't support release year filters,
    this function filters the recommended tracks manually.
    """
    if not min_year and not max_year:
        return tracks  # No filtering needed

    filtered_tracks = []
    track_ids = [track['id'] for track in tracks]
    try:
        for i in range(0, len(track_ids), 50):
            batch_ids = track_ids[i:i+50]
            tracks_info = sp.tracks(batch_ids)['tracks']
            for track in tracks_info:
                release_date = track['album']['release_date']
                release_year = int(release_date.split('-')[0])
                if min_year and release_year < min_year:
                    continue
                if max_year and release_year > max_year:
                    continue
                filtered_tracks.append(track)
            # To avoid hitting rate limits
            time.sleep(0.1)
    except spotipy.exceptions.SpotifyException as e:
        print(f"Error filtering tracks by release year: {e}")
    return filtered_tracks

def main():
    # Check for credentials
    if os.path.exists('credentials.enc'):
        try:
            client_id, client_secret = load_credentials()
        except Exception as e:
            print(f"Error loading credentials: {e}")
            return
    else:
        print("Spotify Developer Credentials are required.")
        client_id = input("Enter your Spotify CLIENT_ID: ").strip()
        client_secret = input("Enter your Spotify CLIENT_SECRET: ").strip()
        save_credentials(client_id, client_secret)
        print("Credentials saved securely.")

    # Spotify authentication
    REDIRECT_URI = 'http://localhost:8888/callback'
    scope = 'playlist-modify-public playlist-modify-private'

    try:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                                       client_secret=client_secret,
                                                       redirect_uri=REDIRECT_URI,
                                                       scope=scope))
    except spotipy.exceptions.SpotifyException as e:
        print(f"Authentication failed: {e}")
        return

    if len(sys.argv) != 2:
        print("Usage: python m3u_recommender_playlist.py <path_to_m3u_playlist_or_audio_file_or_folder>")
        return

    input_path = sys.argv[1]

    if not os.path.exists(input_path):
        print("File or directory not found. Please check the path and try again.")
        return

    tracks = get_input_tracks(input_path)
    if not tracks:
        print("No valid tracks found in the input.")
        return

    input_length = len(tracks)
    print(f"Number of input tracks: {input_length}")

    # Prompt for maximum playlist length
    max_length_input = input(f"Enter the maximum length of the playlist (default is {input_length}): ").strip()
    if max_length_input:
        try:
            max_length = int(max_length_input)
            if max_length < input_length:
                print(f"Maximum length cannot be less than the number of input tracks ({input_length}). Using default.")
                max_length = input_length
        except ValueError:
            print("Invalid input. Using default maximum length.")
            max_length = input_length
    else:
        max_length = input_length

    all_recommended_track_ids = set()
    all_recommended_artist_ids = set()
    batch_size = 5  # Maximum seeds per API call

    print("\nProcessing input and generating recommendations...")

    # Collect additional criteria from the user
    additional_params = {}
    min_release_year = None
    max_release_year = None

    add_criteria = input("Do you want to specify additional criteria for the recommendations? (yes/no): ").strip().lower()
    if add_criteria in ['yes', 'y']:
        # Target Valence
        target_valence = input("Enter target vibe (0.0 - 1.0 / sad - happy, optional): ").strip()
        if target_valence:
            try:
                val = float(target_valence)
                if 0.0 <= val <= 1.0:
                    additional_params['target_valence'] = val
                else:
                    print("Valence must be between 0.0 and 1.0. Skipping this criterion.")
            except ValueError:
                print("Invalid input for valence. Skipping this criterion.")

        # Target Popularity
        target_popularity = input("Enter target popularity (0 - 100, optional): ").strip()
        if target_popularity:
            try:
                val = int(target_popularity)
                if 0 <= val <= 100:
                    additional_params['target_popularity'] = val
                else:
                    print("Popularity must be between 0 and 100. Skipping this criterion.")
            except ValueError:
                print("Invalid input for popularity. Skipping this criterion.")

        # Min Tempo
        min_tempo = input("Enter minimum tempo in BPM (optional): ").strip()
        if min_tempo:
            try:
                val = float(min_tempo)
                additional_params['min_tempo'] = val
            except ValueError:
                print("Invalid input for minimum tempo. Skipping this criterion.")

        # Max Tempo
        max_tempo = input("Enter maximum tempo in BPM (optional): ").strip()
        if max_tempo:
            try:
                val = float(max_tempo)
                additional_params['max_tempo'] = val
            except ValueError:
                print("Invalid input for maximum tempo. Skipping this criterion.")

        # Target Energy
        target_energy = input("Enter target energy (0.0 - 1.0, optional): ").strip()
        if target_energy:
            try:
                val = float(target_energy)
                if 0.0 <= val <= 1.0:
                    additional_params['target_energy'] = val
                else:
                    print("Energy must be between 0.0 and 1.0. Skipping this criterion.")
            except ValueError:
                print("Invalid input for energy. Skipping this criterion.")

        # Target Danceability
        target_danceability = input("Enter target danceability (0.0 - 1.0, optional): ").strip()
        if target_danceability:
            try:
                val = float(target_danceability)
                if 0.0 <= val <= 1.0:
                    additional_params['target_danceability'] = val
                else:
                    print("Danceability must be between 0.0 and 1.0. Skipping this criterion.")
            except ValueError:
                print("Invalid input for danceability. Skipping this criterion.")

        # Minimum Release Year
        min_release_year_input = input("Enter minimum release year (optional): ").strip()
        if min_release_year_input:
            try:
                min_release_year = int(min_release_year_input)
            except ValueError:
                print("Invalid input for minimum release year. Skipping this criterion.")

        # Maximum Release Year
        max_release_year_input = input("Enter maximum release year (optional): ").strip()
        if max_release_year_input:
            try:
                max_release_year = int(max_release_year_input)
            except ValueError:
                print("Invalid input for maximum release year. Skipping this criterion.")
    else:
        print("Proceeding without additional criteria.")

    # Initialize a list to keep track of recommendations per seed track
    recommendations_per_seed = {}

    # Ensure at least one recommendation per seed track
    for idx, track in enumerate(tracks):
        if len(all_recommended_track_ids) >= max_length:
            break
        print(f"\nProcessing seed track {idx + 1}/{input_length}: {track['artist']} - {track['title']}")
        seed_track_id = search_track(sp, track['artist'], track['title'])
        if seed_track_id:
            recommendations = get_recommendations(sp, [seed_track_id], additional_params)
            # Filter by release year if specified
            if min_release_year or max_release_year:
                recommendations = filter_tracks_by_release_year(sp, recommendations, min_release_year, max_release_year)
            for rec_track in recommendations:
                if rec_track['id'] not in all_recommended_track_ids:
                    all_recommended_track_ids.add(rec_track['id'])
                    # Collect artist IDs
                    for artist in rec_track['artists']:
                        all_recommended_artist_ids.add(artist['id'])
                    break  # Ensure at least one recommendation per seed
        else:
            print(f"Seed track not found on Spotify: {track['artist']} - {track['title']}")

    # After ensuring at least one recommendation per seed, fill up to max_length if needed
    if len(all_recommended_track_ids) < max_length:
        remaining = max_length - len(all_recommended_track_ids)
        print(f"\nFetching additional recommendations to reach the desired playlist length ({max_length})...")
        seed_track_ids = []
        for track in tracks:
            track_id = search_track(sp, track['artist'], track['title'])
            if track_id:
                seed_track_ids.append(track_id)
        if seed_track_ids:
            # To comply with Spotify's 5 seed limit, we'll fetch recommendations in batches
            # and accumulate unique tracks until we reach the desired length
            additional_recommendations = get_recommendations(sp, seed_track_ids, additional_params)
            # Filter by release year if specified
            if min_release_year or max_release_year:
                additional_recommendations = filter_tracks_by_release_year(sp, additional_recommendations, min_release_year, max_release_year)
            for rec_track in additional_recommendations:
                if len(all_recommended_track_ids) >= max_length:
                    break
                if rec_track['id'] not in all_recommended_track_ids:
                    all_recommended_track_ids.add(rec_track['id'])
                    # Collect artist IDs
                    for artist in rec_track['artists']:
                        all_recommended_artist_ids.add(artist['id'])
        else:
            print("No valid seed tracks available for additional recommendations.")

    if all_recommended_track_ids:
        try:
            user_id = sp.me()['id']
        except spotipy.exceptions.SpotifyException as e:
            print(f"Error fetching user ID: {e}")
            return

        # New code to print the recommended tracks before creating the playlist
        print("\nRecommended Tracks:")
        recommended_tracks = []
        track_ids_list = list(all_recommended_track_ids)[:max_length]
        for i in range(0, len(track_ids_list), 50):  # Spotify API limit
            batch_ids = track_ids_list[i:i+50]
            try:
                tracks_info = sp.tracks(batch_ids)['tracks']
                for track in tracks_info:
                    track_name = track['name']
                    artists = ', '.join([artist['name'] for artist in track['artists']])
                    print(f"{artists} - {track_name}")
                    recommended_tracks.append({'name': track_name, 'artists': artists})
                # To avoid hitting rate limits
                time.sleep(0.1)
            except spotipy.exceptions.SpotifyException as e:
                print(f"Error fetching track details: {e}")
                continue

        print("\nAnalyzing genres of the recommended tracks...")
        genres = get_genres(sp, list(all_recommended_artist_ids))
        if genres:
            # Count genre frequencies
            genre_counts = Counter(genres)
            # Get top genres
            top_genres = [genre.title() for genre, count in genre_counts.most_common(3)]
            # Build the playlist name
            genre_part = ', '.join(top_genres)
        else:
            genre_part = "Various Genres"

        # Get current date and time
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        # Build default playlist name
        default_playlist_name = f"{genre_part} Playlist {current_datetime}"
        # Ensure playlist name isn't too long
        max_length_name = 100
        if len(default_playlist_name) > max_length_name:
            default_playlist_name = default_playlist_name[:max_length_name]

        print(f"\nSuggested playlist name: '{default_playlist_name}'")
        playlist_name = input("Enter a name for the new playlist (press Enter to accept the suggested name): ").strip()
        if not playlist_name:
            playlist_name = default_playlist_name

        playlist_description = input("Enter a description for the new playlist (optional): ").strip()

        print("\nCreating new playlist on your Spotify account...")
        playlist_id = create_playlist(sp, user_id, playlist_name, playlist_description)
        if not playlist_id:
            print("Failed to create playlist. Exiting.")
            return

        print("Adding recommended tracks to the new playlist...")
        add_tracks_to_playlist(sp, playlist_id, track_ids_list)

        print(f"Playlist '{playlist_name}' created successfully with {len(track_ids_list)} tracks!")
    else:
        print("No recommended tracks found. Playlist not created.")

if __name__ == '__main__':
    main()