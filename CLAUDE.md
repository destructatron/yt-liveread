# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YouTube Live Chat TTS Reader (`yt-liveread`) - A Python CLI application that reads YouTube live chat messages aloud in real-time using Speech Dispatcher (Linux).

## Development Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
# Note: Using Indigo128's fork of chat-downloader (fixes Nov 2025 YouTube parsing issues)
pip install -r requirements.txt

# Install package in editable mode
pip install -e .

# System dependencies (required)
sudo apt install speech-dispatcher python3-speechd espeak-ng

# Verify Speech Dispatcher is running
systemctl --user status speech-dispatcher
spd-say "test"
```

**Important:** As of November 2025, the official `chat-downloader` library has YouTube parsing issues. The project uses Indigo128's fork (https://github.com/Indigo128/chat-downloader) which contains fixes. See https://github.com/xenova/chat-downloader/issues/282

## Running the Application

```bash
# Basic usage
yt-liveread "https://www.youtube.com/watch?v=VIDEO_ID"

# With cookies (required in EU regions due to YouTube consent page)
yt-liveread "URL" --cookies cookies.txt

# Common options
yt-liveread "URL" --voice pico --rate 10 --volume 80 --cookies cookies.txt
```

## Architecture

The application uses a **multi-threaded producer-consumer pattern**:

```
Main Thread (main.py)
├── Parses CLI arguments
├── Creates shared state (queue.Queue, threading.Event)
├── Coordinates shutdown via signal handlers
└── Handles user input (p=pause/resume, q=quit)
    │
    ├── ChatReader Thread (chat_reader.py)
    │   ├── Connects to YouTube via ChatDownloader (with optional cookies)
    │   ├── Receives chat messages in real-time
    │   ├── Formats messages (truncate, filter URLs, add username)
    │   └── Pushes to thread-safe message_queue
    │
    └── TTSSpeaker Thread (tts_speaker.py)
        ├── Reads from message_queue
        ├── Respects pause_event (blocking when paused)
        └── Sends to Speech Dispatcher (speechd.SSIPClient)
```

### Key Threading Components

- **`message_queue` (queue.Queue)**: Thread-safe FIFO queue with maxsize limit. ChatReader produces, TTSSpeaker consumes.
- **`pause_event` (threading.Event)**: Controls TTS playback. Set=running, cleared=paused. TTSSpeaker blocks on `pause_event.wait()`.
- **`shutdown_event` (threading.Event)**: Signals graceful shutdown to all threads.

### Important Implementation Details

1. **Cookie Handling**: Cookies must be passed to `ChatDownloader(**{'cookies': path})` constructor, NOT to `get_chat()`. This is critical for bypassing YouTube's cookie consent page.

2. **Speech Dispatcher Integration**:
   - `python3-speechd` must be installed via system package manager (not pip)
   - The `speechd.SSIPClient` handles its own internal queuing
   - Client must remain alive while messages are being spoken

3. **Message Flow**:
   - ChatReader filters messages by type (`text_message` only)
   - URLs are replaced with `[link]` placeholder
   - Messages truncated to `max_message_length` (default 200 chars)
   - Format: `"{username} says: {message}"` or just `"{message}"` if `--no-username`

## Common Issues

### "Unable to parse initial video data"

This error indicates:
1. YouTube cookie consent page blocking access (most common in EU)
   - **Solution**: Use `--cookies cookies.txt`
2. Stream is not currently live (upcoming/ended)
3. Chat is disabled on the stream

### Cookie Extraction

Users need cookies in Netscape format. Two methods:
1. Browser extension: "Get cookies.txt LOCALLY" (Chrome/Edge) or "cookies.txt" (Firefox)
2. yt-dlp: `yt-dlp --cookies-from-browser chrome --cookies cookies.txt "https://youtube.com"`

### Speech Dispatcher Issues

- Check service: `systemctl --user status speech-dispatcher`
- Test directly: `spd-say "test"`
- Common voice modules: `espeak-ng` (default), `pico` (better quality), `festival`

## Code Structure

- **`config.py`**: Configuration dataclass with validation
- **`chat_reader.py`**: YouTube chat polling thread (ChatReader class)
- **`tts_speaker.py`**: Speech Dispatcher thread (TTSSpeaker class)
- **`main.py`**: CLI entry point, argument parsing, thread coordination

## Critical Implementation Notes

When modifying chat reading:
- Always pass cookies to `ChatDownloader(**{'cookies': path})`, not `get_chat()`
- Catch `ValueError` for parsing errors from chat-downloader
- Maintain helpful error messages guiding users to cookie solution

When modifying TTS:
- Don't close speechd client immediately after `speak()` - messages are queued
- Use `pause_event.wait()` to block when paused (not polling)
- Handle `queue.Empty` exception when getting messages with timeout
- Priority is set to `speechd.Priority.TEXT` (low) to allow screen readers like Orca to interrupt
- Messages are printed to console with `print(f"💬 {text}")` before being spoken

When adding CLI arguments:
- Update both `parse_args()` in main.py and `Config` dataclass
- Add validation in `Config.validate()` if needed
- Update help text in argparse and README.md

## Testing During Development

Since this requires live YouTube streams, testing approach:
1. Find 24/7 live stream (search "lofi hip hop radio" or similar)
2. Verify stream shows red "LIVE" badge and has visible chat
3. Export cookies if in EU region
4. Run: `source venv/bin/activate && yt-liveread "URL" --cookies cookies.txt`
5. Test controls: 'p' to pause/resume, 'q' to quit
