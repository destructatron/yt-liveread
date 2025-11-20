# YouTube Live Chat TTS Reader

A Python CLI application that reads YouTube live chat messages aloud in real-time using text-to-speech.

## Features

- Real-time YouTube live chat reading
- Text-to-speech using Speech Dispatcher (Linux)
- Console output of chat messages alongside speech
- Low-priority speech (allows screen readers like Orca to interrupt)
- Configurable voice, rate, pitch, and volume
- Simple pause/resume controls
- Cookie support for bypassing YouTube consent pages
- Automatic message formatting and URL filtering

## Requirements

### System Dependencies

**Debian/Ubuntu:**
```bash
sudo apt update
sudo apt install speech-dispatcher python3-speechd espeak-ng
```

**Fedora/RHEL:**
```bash
sudo dnf install speech-dispatcher python3-speechd espeak-ng
```

### Virtual environment notes

When you create the virtual environment, use --system-site-packages. The reason for this is because the Python speechd bindings aren't readily available on pipy. This will add the speechd bindings and your system level site packages, while still letting you install the other dependencies that distributions won't have.

## Installation

### Install from source

```bash
# Clone or navigate to the project directory
cd yt-liveread

# Install Python dependencies
# Note: Currently using a fork of chat-downloader due to YouTube parsing issues
pip install -r requirements.txt

# Install the package
pip install -e .
```

**Note:** Due to recent YouTube changes (November 2025), we're temporarily using a community fork of `chat-downloader` that fixes parsing issues. See [issue #282](https://github.com/xenova/chat-downloader/issues/282) for details.

## Usage

### Basic Usage

```bash
yt-liveread "https://www.youtube.com/watch?v=VIDEO_ID"
```

### ⚠️ Important: Cookie Consent Issue

If you get an "Unable to parse initial video data" error, it's likely due to YouTube's cookie consent page (especially common in EU regions). You need to provide cookies:

```bash
yt-liveread "URL" --cookies cookies.txt
```

**How to get cookies:**

1. **Install a browser extension** to export cookies:
   - Chrome/Edge: "Get cookies.txt LOCALLY"
   - Firefox: "cookies.txt"

2. **Export cookies**:
   - Click the extension icon while on youtube.com
   - Export/download cookies in Netscape format
   - Save as `cookies.txt`

3. **Use with the application**:
   ```bash
   yt-liveread "https://www.youtube.com/watch?v=VIDEO_ID" --cookies cookies.txt
   ```

**Alternative method using yt-dlp:**
```bash
# Install yt-dlp if you haven't
pip install yt-dlp

# Extract cookies from your browser
yt-dlp --cookies-from-browser chrome --cookies cookies.txt "https://youtube.com"
```

### With Options

```bash
# Adjust speech rate (faster)
yt-liveread "URL" --rate 20

# Skip reading usernames
yt-liveread "URL" --no-username

# Limit message length
yt-liveread "URL" --max-length 150

# Combine options
yt-liveread "URL" --voice pico --rate 10 --volume 80
```

### Controls

While the application is running:

- **p** - Pause/Resume speech
- **q** - Quit application
- **Ctrl+C** - Also quits the application

## Command-Line Options

```
usage: yt-liveread [-h] [--voice {espeak-ng,pico,festival}] [--rate RATE]
                   [--volume VOLUME] [--pitch PITCH] [--max-length MAX_LENGTH]
                   [--no-username] [--language LANGUAGE] [--queue-size QUEUE_SIZE]
                   [--cookies COOKIES]
                   url

positional arguments:
  url                   YouTube live stream URL

optional arguments:
  -h, --help            show this help message and exit
  --voice {espeak-ng,pico,festival}
                        TTS voice engine (default: espeak-ng)
  --rate RATE           Speech rate from -100 (slow) to 100 (fast) (default: 0)
  --volume VOLUME       Volume from 0 to 100 (default: 100)
  --pitch PITCH         Voice pitch from -100 (low) to 100 (high) (default: 0)
  --max-length MAX_LENGTH
                        Maximum message length to speak (default: 200)
  --no-username         Skip reading usernames, only read message text
  --language LANGUAGE   TTS language code (default: en)
  --queue-size QUEUE_SIZE
                        Maximum message queue size (default: 50)
  --cookies COOKIES     Path to cookies file (Netscape format) to bypass YouTube consent page
```

## Troubleshooting

### "python3-speechd is not installed" error

Make sure you installed the system package (not via pip):
```bash
sudo apt install python3-speechd
```

### "Invalid YouTube URL" error

Make sure the URL is in one of these formats:
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/live/VIDEO_ID`

### "Unable to parse initial video data" error

This error typically means the stream is not currently live or doesn't have chat available. Check if it is still live or if it's upcoming. If either of these situations happens, there's no chat area to parse.

### Chat not connecting (other issues)

- Verify the URL format is correct
- Try accessing the URL in your browser to confirm it loads
- Check your internet connection
- Some streams may have region restrictions

## Future Enhancements

Potential features for future versions:

- Cross-platform support (Windows with SAPI, macOS with say)
- Message filtering (keywords, super chats, moderators)
- Rate limiting for very active chats
- Configuration file support
- GUI interface
- Message prioritization

## Credits

- Uses [chat-downloader](https://github.com/xenova/chat-downloader) for YouTube chat access
- Uses [Speech Dispatcher](https://github.com/brailcom/speechd) for text-to-speech on Linux
