import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import re
import sys
from cryptography.fernet import Fernet
import datetime
from collections import Counter


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


def search_track(sp, artist, title):
    query = f'artist:{artist} track:{title}'
    result = sp.search(q=query, type='track', limit=1)
    tracks = result['tracks']['items']
    if tracks:
        return tracks[0]['id']
    else:
        return None


def get_recommendations(sp, seed_tracks, **kwargs):
    recommendations = sp.recommendations(seed_tracks=seed_tracks, limit=10, **kwargs)
    return recommendations['tracks']


def create_playlist(sp, user_id, name, description=''):
    playlist = sp.user_playlist_create(user=user_id, name=name, public=False, description=description)
    return playlist['id']


def add_tracks_to_playlist(sp, playlist_id, track_ids):
    # Spotify API allows adding up to 100 tracks at a time
    for i in range(0, len(track_ids), 100):
        sp.playlist_add_items(playlist_id, track_ids[i:i+100])


def get_genres(sp, artist_ids):
    genres = []
    # Batch the artist IDs
    for i in range(0, len(artist_ids), 50):
        batch_ids = artist_ids[i:i+50]
        artists = sp.artists(batch_ids)['artists']
        for artist in artists:
            genres.extend(artist['genres'])
    return genres


def main():
    # Check for credentials
    if os.path.exists('credentials.enc'):
        client_id, client_secret = load_credentials()
    else:
        print("Spotify Developer Credentials are required.")
        client_id = input("Enter your Spotify CLIENT_ID: ").strip()
        client_secret = input("Enter your Spotify CLIENT_SECRET: ").strip()
        save_credentials(client_id, client_secret)
        print("Credentials saved securely.")

    # Spotify authentication
    REDIRECT_URI = 'http://localhost:8888/callback'
    scope = 'playlist-modify-public playlist-modify-private'

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                                   client_secret=client_secret,
                                                   redirect_uri=REDIRECT_URI,
                                                   scope=scope))

    if len(sys.argv) != 2:
        print("Usage: python m3u_recommender_playlist.py <path_to_m3u_playlist>")
        return

    playlist_path = sys.argv[1]

    if not os.path.exists(playlist_path):
        print("File not found. Please check the path and try again.")
        return

    tracks = parse_m3u(playlist_path)
    if not tracks:
        print("No tracks found in the playlist.")
        return

    all_recommended_track_ids = set()
    all_recommended_artist_ids = set()
    batch_size = 5

    print("\nProcessing playlist and generating recommendations...")

    # Collect additional criteria from the user
    additional_params = {}
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
    else:
        print("Proceeding without additional criteria.")

    for i in range(0, len(tracks), batch_size):
        batch_tracks = tracks[i:i+batch_size]
        seed_track_ids = []

        # Search for Spotify IDs for seed tracks
        for track in batch_tracks:
            track_id = search_track(sp, track['artist'], track['title'])
            if track_id:
                seed_track_ids.append(track_id)
            else:
                print(f"Seed track not found on Spotify: {track['artist']} - {track['title']}")

        if seed_track_ids:
            recommendations = get_recommendations(sp, seed_track_ids, **additional_params)
            for rec_track in recommendations:
                all_recommended_track_ids.add(rec_track['id'])
                # Collect artist IDs
                for artist in rec_track['artists']:
                    all_recommended_artist_ids.add(artist['id'])
        else:
            print(f"No valid seed tracks found in batch starting at index {i}. Skipping recommendations for this batch.")

    if all_recommended_track_ids:
        user_id = sp.me()['id']

        # New code to print the recommended tracks before creating the playlist
        print("\nRecommended Tracks:")
        recommended_tracks = []
        track_ids_list = list(all_recommended_track_ids)
        for i in range(0, len(track_ids_list), 50):  # Spotify API limit
            batch_ids = track_ids_list[i:i+50]
            tracks_info = sp.tracks(batch_ids)['tracks']
            for track in tracks_info:
                track_name = track['name']
                artists = ', '.join([artist['name'] for artist in track['artists']])
                print(f"{artists} - {track_name}")
                recommended_tracks.append({'name': track_name, 'artists': artists})

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
        max_length = 100
        if len(default_playlist_name) > max_length:
            default_playlist_name = default_playlist_name[:max_length]

        print(f"\nSuggested playlist name: '{default_playlist_name}'")
        playlist_name = input("Enter a name for the new playlist (press Enter to accept the suggested name): ").strip()
        if not playlist_name:
            playlist_name = default_playlist_name

        playlist_description = input("Enter a description for the new playlist (optional): ").strip()

        print("\nCreating new playlist on your Spotify account...")
        playlist_id = create_playlist(sp, user_id, playlist_name, playlist_description)

        print("Adding recommended tracks to the new playlist...")
        add_tracks_to_playlist(sp, playlist_id, track_ids_list)

        print(f"Playlist '{playlist_name}' created successfully with {len(all_recommended_track_ids)} tracks!")
    else:
        print("No recommended tracks found. Playlist not created.")


if __name__ == '__main__':
    main()