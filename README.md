# Seedify

![Spotify](https://img.shields.io/badge/Spotify-1DB954?style=for-the-badge&logo=spotify&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Prerequisites](#prerequisites)
  - [Spotify Developer Account](#spotify-developer-account)
  - [Python Installation](#python-installation)
    - [macOS (Using Homebrew)](#macos-using-homebrew)
    - [Windows](#windows)
- [Installation](#installation)
  - [Clone the Repository](#clone-the-repository)
  - [Set Up Virtual Environment](#set-up-virtual-environment)
  - [Install Dependencies](#install-dependencies)
- [Usage](#usage)
  - [Preparing Input](#preparing-input)
    - [M3U Playlists](#m3u-playlists)
    - [Single Audio Files](#single-audio-files)
    - [Folders Containing Audio Files](#folders-containing-audio-files)
  - [Running the Script](#running-the-script)
  - [User Prompts](#user-prompts)
    - [Additional Criteria](#additional-criteria)
    - [Maximum Playlist Length](#maximum-playlist-length)
    - [Playlist Naming](#playlist-naming)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Introduction

**Seedify** is a Python-based tool that generates Spotify playlists based on your existing M3U playlists, individual audio files, or folders containing audio files. By leveraging the Spotify API, Seedify recommends tracks tailored to your musical preferences, ensuring a personalized and enjoyable listening experience.

## Features

- **Flexible Input:** Supports M3U playlists, individual audio files, and entire folders (searched recursively).
- **Secure Credentials:** Encrypts and securely stores Spotify Developer credentials.
- **Customized Recommendations:** Allows specification of criteria like valence, popularity, tempo, energy, danceability, and release year.
- **Playlist Length Control:** Ensures the playlist length meets user preferences, defaulting to the number of input tracks.
- **Genre-Based Naming:** Suggests playlist names based on the most common genres among recommended tracks.
- **Robust Error Handling:** Provides meaningful feedback and handles API limitations gracefully.

## Prerequisites

### Spotify Developer Account

To use Seedify, you need a Spotify Developer account and a Spotify Premium subscription.

1. **Create a Spotify Developer Account:**
   - Visit the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
   - Log in with your Spotify Premium credentials or create a Spotify account if you don't have one.

2. **Create an Application:**
   - Click on **"Create an App"**.
   - Provide an **App Name** and **App Description**.
   - Agree to the terms and click **"Create"**.

3. **Retrieve Credentials:**
   - In the **"Overview"** tab, note down your **Client ID** and **Client Secret**.
   - **Set Redirect URI:** Go to **"Edit Settings"** and add `http://localhost:8888/callback` to the **Redirect URIs**. Click **"Save"**.

### Python Installation

#### macOS (Using Homebrew)

1. **Install Homebrew (if not already installed):**

   Open Terminal and run:

   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Python:**

   ```bash
   brew install python
   ```

3. **Verify Installation:**

   ```bash
   python3 --version
   ```

#### Windows

1. **Download Python Installer:**

   - Visit the [official Python website](https://www.python.org/downloads/windows/).
   - Download the latest Python 3.x installer.

2. **Run the Installer:**

   - Double-click the installer.
   - **Important:** Check **"Add Python 3.x to PATH"**.
   - Click **"Install Now"**.

3. **Verify Installation:**

   Open Command Prompt and run:

   ```bash
   python --version
   ```

   If `python` points to Python 3.x, you're all set.

## Installation

### Clone the Repository

```bash
git clone https://github.com/yourusername/seedify.git
cd seedify
```

*Replace `yourusername` with the actual GitHub username if applicable.*

### Set Up Virtual Environment

It's recommended to use a virtual environment to manage dependencies.

#### macOS and Windows

1. **Create a Virtual Environment:**

   ```bash
   python3 -m venv venv
   ```

   On Windows:

   ```bash
   python -m venv venv
   ```

2. **Activate the Virtual Environment:**

   - **macOS:**

     ```bash
     source venv/bin/activate
     ```

   - **Windows:**

     ```bash
     venv\Scripts\activate
     ```

   You should see `(venv)` prefixed in your terminal.

### Install Dependencies

Ensure you have a `requirements.txt` file present. Install the required Python packages using `pip`:

```bash
pip install -r requirements.txt
```

*If `requirements.txt` is not present, create one with the following content:*

```txt
spotipy
cryptography
mutagen
```

Then run the `pip install` command again.

## Usage

Seedify can process M3U playlists, individual audio files, or folders to generate a Spotify playlist with recommended tracks.

### Preparing Input

#### M3U Playlists

1. **Create or Obtain an M3U Playlist:**
   - Use a media player like VLC to export your current playlist as an M3U file.
   - Alternatively, create a text file with the `.m3u` extension listing the paths to your audio files.

2. **Ensure Correct Formatting:**
   - Each track should have proper metadata for accurate parsing.

#### Single Audio Files

1. **Supported Formats:**
   - `.mp3`, `.flac`, `.wav`, `.m4a`, `.aac`, `.ogg`

2. **Metadata Requirements:**
   - Ensure audio files have accurate **Artist** and **Title** tags using tagging software like [MP3Tag](https://www.mp3tag.de/en/) or [MusicBrainz Picard](https://picard.musicbrainz.org/).

#### Folders Containing Audio Files

1. **Organize Your Music:**
   - Place all desired audio files within a single folder or multiple subfolders.

2. **Metadata Requirements:**
   - Ensure accurate metadata tags for better track identification.

### Running the Script

1. **Activate the Virtual Environment:**

   - **macOS:**

     ```bash
     source venv/bin/activate
     ```

   - **Windows:**

     ```bash
     venv\Scripts\activate
     ```

2. **Run the Script:**

   ```bash
   python seedify.py <path_to_m3u_playlist_or_audio_file_or_folder>
   ```

   *Replace `<path_to_m3u_playlist_or_audio_file_or_folder>` with your input path.*

   **Examples:**

   - **M3U Playlist:**

     ```bash
     python seedify.py ~/Music/MyPlaylist.m3u
     ```

   - **Single Audio File:**

     ```bash
     python seedify.py ~/Music/Songs/FavoriteSong.mp3
     ```

   - **Folder:**

     ```bash
     python seedify.py ~/Music/Albums/
     ```

### User Prompts

During execution, Seedify will guide you through several prompts to customize your playlist.

#### Additional Criteria

Specify additional criteria to refine recommendations:

- **Target Vibe (Valence):** `0.0` (sad) to `1.0` (happy)
- **Target Popularity:** `0` (least popular) to `100` (most popular)
- **Tempo (BPM):** Minimum and/or maximum
- **Energy:** `0.0` (least energetic) to `1.0` (most energetic)
- **Danceability:** `0.0` (least danceable) to `1.0` (most danceable)
- **Release Year:** Minimum and/or maximum

*Example Prompt Flow:*

```plaintext
Do you want to specify additional criteria for the recommendations? (yes/no): yes
Enter target vibe (0.0 - 1.0 / sad - happy, optional): 0.7
Enter target popularity (0 - 100, optional): 50
Enter minimum tempo in BPM (optional): 120
Enter maximum tempo in BPM (optional): 140
Enter target energy (0.0 - 1.0, optional): 0.6
Enter target danceability (0.0 - 1.0, optional): 0.8
Enter minimum release year (optional): 2015
Enter maximum release year (optional): 2023
```

#### Maximum Playlist Length

Specify the maximum number of tracks. Defaults to the number of input seed tracks.

*Example:*

```plaintext
Enter the maximum length of the playlist (default is 10): 20
```

#### Playlist Naming

Seedify suggests a playlist name based on common genres. You can accept the suggestion or provide your own.

*Example:*

```plaintext
Suggested playlist name: 'Pop, Rock, Indie Playlist 2024-04-27 15:30'
Enter a name for the new playlist (press Enter to accept the suggested name): My Custom Playlist
```

You can also add an optional description for your playlist.

## Troubleshooting

### 1. **Spotify API Error: 400 Bad Request**

**Cause:**  
Exceeded the maximum number of seed tracks (Spotify allows up to 5).

**Solution:**  
Ensure you're using the latest version of Seedify, which batches seed tracks into groups of 5.

### 2. **Authentication Failed**

**Cause:**  
Incorrect `CLIENT_ID` or `CLIENT_SECRET`, or incorrect Redirect URI.

**Solution:**  
- Verify your Spotify Developer credentials.
- Ensure the Redirect URI `http://localhost:8888/callback` is set in your Spotify Developer Dashboard.

### 3. **Unsupported Audio Format**

**Cause:**  
Audio file format not supported.

**Solution:**  
Use supported formats: `.mp3`, `.flac`, `.wav`, `.m4a`, `.aac`, `.ogg`.

### 4. **Missing Metadata**

**Cause:**  
Audio files lack proper **Artist** and **Title** tags.

**Solution:**  
Use tagging software like [MP3Tag](https://www.mp3tag.de/en/) or [MusicBrainz Picard](https://picard.musicbrainz.org/) to add or correct metadata.

### 5. **Rate Limiting**

**Cause:**  
Exceeding Spotify's rate limits due to too many rapid API requests.

**Solution:**  
Seedify includes short pauses between API calls. If issues persist, consider increasing the sleep duration in the script.

### 6. **Missing Dependencies**

**Cause:**  
Required Python packages are not installed.

**Solution:**  
Ensure you've run `pip install -r requirements.txt` within the activated virtual environment.

## Contributing

Contributions are welcome! Follow these steps:

1. **Fork the Repository:** Click the **Fork** button at the top-right corner.
2. **Clone Your Fork:**

   ```bash
   git clone https://github.com/yourusername/seedify.git
   cd seedify
   ```

3. **Create a New Branch:**

   ```bash
   git checkout -b feature/YourFeatureName
   ```

4. **Make Your Changes:** Implement your feature or fix.
5. **Commit Your Changes:**

   ```bash
   git commit -m "Add feature: Your Feature Description"
   ```

6. **Push to Your Fork:**

   ```bash
   git push origin feature/YourFeatureName
   ```

7. **Create a Pull Request:** Navigate to the original repository and open a pull request detailing your changes.

## License

This project is licensed under the [MIT License](LICENSE).

## Contact

For questions or suggestions, feel free to open an issue or reach out to [jannik.assfalg@gmail.com](mailto:jannik.assfalg@gmail.com).

---

**Happy Listening! 🎶**