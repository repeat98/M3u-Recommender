import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import re
import sys
from cryptography.fernet import Fernet


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
        for i in range(len(lines)):
            line = lines[i].strip()
            if line.startswith('#EXTINF:'):
                info = line.split('#EXTINF:')[1]
                # Extract artist and title
                match = re.match(r'[\d-]+,(.*) - (.*)', info)
                if match:
                    artist = match.group(1).strip()
                    title = match.group(2).strip()
                    tracks.append({'artist': artist, 'title': title})
                else:
                    # Handle cases where the format is different
                    title_info = info.split(',', 1)[-1]
                    if ' - ' in title_info:
                        artist, title = title_info.split(' - ', 1)
                        tracks.append({'artist': artist.strip(), 'title': title.strip()})
        return tracks


def search_track(sp, artist, title):
    query = f'artist:{artist} track:{title}'
    result = sp.search(q=query, type='track', limit=1)
    tracks = result['tracks']['items']
    if tracks:
        return tracks[0]['id']
    else:
        return None


def get_recommendations(sp, seed_tracks):
    recommendations = sp.recommendations(seed_tracks=seed_tracks, limit=10)
    return recommendations['tracks']


def create_playlist(sp, user_id, name, description=''):
    playlist = sp.user_playlist_create(user=user_id, name=name, public=False, description=description)
    return playlist['id']


def add_tracks_to_playlist(sp, playlist_id, track_ids):
    # Spotify API allows adding up to 100 tracks at a time
    for i in range(0, len(track_ids), 100):
        sp.playlist_add_items(playlist_id, track_ids[i:i+100])


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
    batch_size = 5

    print("\nProcessing playlist and generating recommendations...")

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
            recommendations = get_recommendations(sp, seed_track_ids)
            for rec_track in recommendations:
                all_recommended_track_ids.add(rec_track['id'])
        else:
            print(f"No valid seed tracks found in batch starting at index {i}. Skipping recommendations for this batch.")

    if all_recommended_track_ids:
        user_id = sp.me()['id']
        playlist_name = input("\nEnter a name for the new playlist: ").strip()
        playlist_description = input("Enter a description for the new playlist (optional): ").strip()

        print("\nCreating new playlist on your Spotify account...")
        playlist_id = create_playlist(sp, user_id, playlist_name, playlist_description)

        print("Adding recommended tracks to the new playlist...")
        add_tracks_to_playlist(sp, playlist_id, list(all_recommended_track_ids))

        print(f"Playlist '{playlist_name}' created successfully with {len(all_recommended_track_ids)} tracks!")
    else:
        print("No recommended tracks found. Playlist not created.")


if __name__ == '__main__':
    main()