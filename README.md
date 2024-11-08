# M3U Recommender Playlist Generator

## Overview

This script reads an `.m3u` playlist file, parses the track information, searches for those tracks on Spotify, generates song recommendations based on them, and creates a new playlist in your Spotify account with the recommended tracks.

## Features

- **Parse M3U Playlists**: Extracts artist and title information from `.m3u` files.
- **Spotify Integration**: Searches for tracks and generates recommendations using the Spotify API.
- **Secure Credential Storage**: Encrypts and stores your Spotify API credentials securely.
- **Automated Playlist Creation**: Creates a new playlist in your Spotify account and adds the recommended tracks.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
  - [1. Install Python Packages](#1-install-python-packages)
  - [2. Set Up a Spotify Developer Account](#2-set-up-a-spotify-developer-account)
  - [3. Prepare the Script](#3-prepare-the-script)
  - [4. Prepare Your M3U Playlist File](#4-prepare-your-m3u-playlist-file)
  - [5. Run the Script](#5-run-the-script)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)
- [Security Note](#security-note)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Prerequisites

- **Python 3.x** installed on your system.
- **Spotify Account**: A free or premium Spotify account.
- **Spotify Developer Account**: To obtain `CLIENT_ID` and `CLIENT_SECRET`.

## Setup Instructions

### 1. Install Python Packages

Install the required Python packages using `pip`:

```bash
pip install spotipy cryptography
```

### 2. Set Up a Spotify Developer Account

To interact with the Spotify API, you need to create a Spotify Developer account and register an application to obtain your `CLIENT_ID` and `CLIENT_SECRET`.

#### Steps:

1. **Create a Spotify Account** (if you don't have one):

   - Go to [Spotify Sign Up](https://www.spotify.com/signup/) and create an account.

2. **Create a Spotify Developer Account**:

   - Visit the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
   - Log in with your Spotify account credentials.
   - Accept the terms and conditions if prompted.

3. **Create a New Application**:

   - Click on **"Create An App"**.
   - Fill in the details:
     - **App Name**: Choose a name (e.g., "M3U Recommender Playlist Generator").
     - **App Description**: Briefly describe your app.
   - Agree to the terms and click **"Create"**.

4. **Edit Settings**:

   - In your app dashboard, click on **"Edit Settings"**.
   - Under **Redirect URIs**, add: `http://localhost:8888/callback`
     - This URI must match the `REDIRECT_URI` in the script.
   - Click **"Add"** and then **"Save"**.

5. **Obtain Credentials**:

   - In the app dashboard, you'll find your **Client ID**.
   - Click on **"Show Client Secret"** to reveal your **Client Secret**.
   - **Important**: Keep these credentials secure.

### 3. Prepare the Script

1. **Save the Script**:

   - Save the provided script as `m3u_recommender_playlist.py`.

2. **Initial Run to Save Credentials**:

   - Open a terminal and run:

     ```bash
     python m3u_recommender_playlist.py
     ```

   - When prompted, enter your **Client ID** and **Client Secret**.
   - The credentials will be encrypted and saved in `credentials.enc`.

### 4. Prepare Your M3U Playlist File

- Ensure you have an `.m3u` playlist file with the correct format.
- Place the `.m3u` file in a directory accessible from the script.

### 5. Run the Script

Execute the script with the path to your `.m3u` file:

```bash
python m3u_recommender_playlist.py /path/to/your/playlist.m3u
```

- Replace `/path/to/your/playlist.m3u` with the actual path.

## Usage

1. **Run the Script**:

   ```bash
   python m3u_recommender_playlist.py /path/to/your/playlist.m3u
   ```

2. **Authentication**:

   - A web browser window will open for Spotify authentication.
   - Log in and authorize the app.

3. **Follow Prompts**:

   - Enter a name for the new playlist when prompted.
   - Optionally, add a description.

4. **Completion**:

   - The script will process the playlist, generate recommendations, and create a new playlist in your Spotify account.
   - Upon success, a message will display the number of tracks added.

## Troubleshooting

- **Authentication Issues**:

  - Ensure the `REDIRECT_URI` matches in both the script and Spotify Developer Dashboard.
  - If the browser doesn't open automatically, copy the provided URL into your browser.

- **Module Not Found Error**:

  - Install missing packages:

    ```bash
    pip install spotipy cryptography
    ```

- **Invalid Client ID/Secret**:

  - Double-check the credentials entered during the initial run.
  - Delete `credentials.enc` and `key.key`, then rerun the script to re-enter credentials.

- **No Tracks Found**:

  - Verify the `.m3u` file has the correct format.
  - Ensure the file contains tracks with artist and title information.

- **API Rate Limits**:

  - If you encounter rate limit errors, wait for a few minutes before retrying.

## Security Note

- **Credential Encryption**:

  - Your `CLIENT_ID` and `CLIENT_SECRET` are encrypted using the `cryptography` library.
  - The encryption key is stored in `key.key`, and encrypted credentials are in `credentials.enc`.
  - Do not share these files with others.

## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the Repository**:

   - Create a fork on GitHub.

2. **Create a Branch**:

   - For new features: `git checkout -b feature/your-feature-name`
   - For bug fixes: `git checkout -b bugfix/your-bugfix-name`

3. **Commit Your Changes**:

   - Write clear and concise commit messages.

4. **Push to Your Fork**:

   - `git push origin your-branch-name`

5. **Submit a Pull Request**:

   - Provide a detailed description of your changes.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgments

- **[Spotipy](https://spotipy.readthedocs.io/)**: A lightweight Python library for the Spotify Web API.
- **[Cryptography](https://cryptography.io/en/latest/)**: A package to encrypt and decrypt data.

---

Feel free to customize and enhance this script to suit your needs. Enjoy your personalized music recommendations!