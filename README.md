# WhisperTube

A modern, privacy‑friendly tool for downloading transcripts from YouTube videos and channels, powered by OpenAI Whisper. Available in both **Command-Line** and **Modern GUI** versions.

**Project Folder**: `WhisperTube`

## Features

- **Single Video Mode**: Download and display transcript for individual YouTube videos
- **Channel Scrape Mode**: Bulk download transcripts from YouTube channels
- **AI-Powered Transcription**: Downloads video audio and generates transcripts using OpenAI's Whisper AI
- **CSV Output**: Exports results to structured CSV files on your Desktop
- **Progress Tracking**: Visual progress bar for bulk operations
- **Comprehensive Error Handling**: Gracefully handles missing or disabled transcripts

## Installation

1. **Install Python 3.7+** if not already installed.

2. **Install FFmpeg** (required for audio processing):
   - **Windows**: Download from https://ffmpeg.org/download.html or use `winget install ffmpeg`
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg` (Ubuntu/Debian) or `sudo yum install ffmpeg` (CentOS/RHEL)

3. **Install required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   Or install manually:
   ```bash
   pip install yt-dlp openai-whisper pydub tqdm
   ```

## Usage

### 🖥️ GUI Version (Recommended)

Run the modern graphical interface:

```bash
# Windows
run_gui.bat

# Or directly with Python
python run_gui.py
```

**GUI Features:**
- 🎨 **Modern Dark Theme** - Sleek, professional interface
- ⚙️ **Easy Configuration** - Radio buttons and dropdowns for all settings
- 📁 **File Browser** - Easy folder selection
- 📊 **Real-time Progress** - Live updates with timestamps
- 🚀 **One-Click Operation** - Start scraping with a single button
- 📂 **Organized Storage** - Automatic folder structure for each scraping session
- 💾 **Audio Management** - Option to keep or clean up downloaded audio files

### 💻 Command Line Version

Run the command-line interface:

```bash
# Navigate to the project folder
cd WhisperTube

# Run the scraper
python scraper.py
```

### Whisper Model Selection

The script will prompt you to choose a Whisper model:

1. **tiny** - Fastest, least accurate (good for testing)
2. **base** - Good balance of speed/accuracy (recommended)
3. **small** - Better accuracy, slower
4. **medium** - Best accuracy, requires more RAM/time
5. **large-v3** - Best accuracy, requires most RAM/time

**Recommendation**: Start with "base" for good balance of speed and accuracy.

### Single Video Mode

1. Choose option `1` (Single video)
2. Enter a YouTube video URL
3. The script will display the video title, view count, duration, and full transcript

**Supported URL formats:**
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/shorts/VIDEO_ID`
- `https://www.youtube.com/embed/VIDEO_ID`

### Channel Scrape Mode

1. Choose option `2` (Entire channel)
2. Enter a YouTube channel URL
3. Specify the number of videos to scrape
4. Choose video type preference:
   - **Longform videos**: Regular YouTube videos
   - **Shorts**: YouTube Shorts
   - **Both**: All video types
5. The script will process all videos and create a CSV file

**Supported channel URL formats:**
- `https://www.youtube.com/channel/CHANNEL_ID`
- `https://www.youtube.com/c/channel_name`
- `https://www.youtube.com/@username`
- `https://www.youtube.com/user/username`

### Output

**Single Video Mode**: Transcripts are displayed directly in the console with video metadata.

**Channel Mode**: CSV files are saved to `Desktop/YouTube_Transcripts/` with enhanced columns:
- **Title**: Video title
- **Video URL**: Direct link to the video
- **View Count**: Number of views
- **Duration (seconds)**: Video length in MM:SS format
- **Uploader**: Channel name
- **Upload Date**: When the video was uploaded
- **Description**: Video description (first 200 characters)
- **Transcript**: Full transcript text (or error message if unavailable)
- **Transcript Type**: Method used (AI Generated, etc.)
- **Character Count**: Length of transcript
- **Processing Date**: When the transcript was generated

## Transcript Priority Logic

The scraper tries to find transcripts in this exact order:

1. **Manually created English transcripts** (highest priority)
2. **Auto-generated English transcripts** 
3. **First available transcript in any other language**
4. **Error message** if no transcripts found

## Error Handling

The script gracefully handles various scenarios:
- Videos with disabled transcripts
- Videos without any available transcripts
- Network errors and API failures
- Invalid URLs and parsing errors
- Keyboard interrupts (Ctrl+C)

When transcripts can't be downloaded, the CSV will contain descriptive error messages in the Transcript column.

## Dependencies

- **yt-dlp**: For downloading video audio and extracting metadata
- **openai-whisper**: For AI-powered speech-to-text transcription
- **pydub**: For audio processing and format conversion
- **tqdm**: For progress bars during bulk operations
- **FFmpeg**: For audio format conversion (system dependency)
- **PyTorch**: Required by Whisper for AI model processing

## Troubleshooting

**"Missing required dependency" error:**
- Run `pip install -r requirements.txt`

**"No videos found or error accessing channel":**
- Check your channel URL format
- Some channels may be private or have restricted access
- Try with fewer videos

**"No transcript available":**
- The channel/video has disabled transcripts
- Try a different video or channel

**Script runs slowly:**
- Consider reducing the number of videos for bulk scraping
- Network speed affects download performance

## Examples

**Single Video Example:**
```
Enter YouTube video URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

**Channel Example:**
```
Enter YouTube channel URL: https://www.youtube.com/@veritasium
Number of videos to scrape: 25
Video type preference: 1 (Longform videos)
```

## File Structure

```
WhisperTube/
├── youtube_scraper_gui.py    # Modern GUI application (recommended)
├── scraper.py               # Command-line version
├── run_gui.py              # GUI launcher script
├── run_gui.bat             # Windows batch file for GUI
├── requirements.txt        # Dependencies
└── README.md              # Documentation
```

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run GUI version:**
   ```bash
   # Navigate to the project folder
   cd YoutubeScraperTranscripts
   
   # Windows
   run_gui.bat
   
   # Or directly
   python run_gui.py
   ```

3. **Configure settings** in the GUI and start scraping!

## 📂 Organized Folder Structure

The GUI creates a well-organized folder structure for each scraping session:

```
YouTube_Transcripts/
├── channel_veritasium_20241228_143022/           # Channel session folder
│   ├── youtube_transcripts_20241228_143022.csv   # Main CSV file
│   ├── 7jg0j_7NCGA_DON'T_CHECK_THE_SOUND/       # Individual video folder
│   │   ├── 7jg0j_7NCGA.wav                      # Audio file (if kept)
│   │   ├── 7jg0j_7NCGA_transcript.txt           # Transcript text
│   │   └── 7jg0j_7NCGA_metadata.txt             # Video metadata
│   ├── wSJ630BnZW4_DON'T_CLICK_THE_SOUND/       # Another video folder
│   │   ├── wSJ630BnZW4.wav
│   │   ├── wSJ630BnZW4_transcript.txt
│   │   └── wSJ630BnZW4_metadata.txt
│   └── ...
├── single_video_veritasium_20241228_150000/      # Single video session folder
│   └── 7jg0j_7NCGA_DON'T_CHECK_THE_SOUND/       # Video folder
│       ├── 7jg0j_7NCGA.wav
│       ├── 7jg0j_7NCGA_transcript.txt
│       └── 7jg0j_7NCGA_metadata.txt
└── channel_another_channel_20241228_160000/      # Another channel session
    └── ...
```

**Folder Naming:**
- **Single video folders**: `single_video_{channel_name}_{timestamp}`
- **Channel folders**: `channel_{channel_name}_{timestamp}`
- **Video folders**: `{video_id}_{cleaned_title}`
- **Files**: `{video_id}_{type}.{extension}`

**Benefits:**
- 🗂️ **Easy Organization** - Each scraping session has its own folder
- 📁 **Individual Videos** - Each video gets its own subfolder
- 💾 **Complete Data** - Audio, transcript, and metadata all together
- 🔍 **Easy Navigation** - Clear folder structure for finding content

## License

This script is for educational and personal use only. Respect YouTube's terms of service and applicable copyright laws when using this tool.

## Contributing

Feel free to submit issues and enhancement requests!
