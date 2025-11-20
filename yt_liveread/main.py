#!/usr/bin/env python3
"""YouTube Live Chat TTS Reader - Main Entry Point"""

import argparse
import queue
import re
import signal
import sys
import threading

from .chat_reader import ChatReader
from .config import Config
from .tts_speaker import TTSSpeaker


def validate_youtube_url(url: str) -> str:
    """Validate YouTube URL format

    Args:
        url: URL to validate

    Returns:
        The validated URL

    Raises:
        argparse.ArgumentTypeError: If URL is invalid
    """
    # Accept various YouTube URL formats
    patterns = [
        r"^https?://(www\.)?youtube\.com/watch\?v=[\w-]+",
        r"^https?://youtu\.be/[\w-]+",
        r"^https?://(www\.)?youtube\.com/live/[\w-]+",
    ]

    for pattern in patterns:
        if re.match(pattern, url):
            return url

    raise argparse.ArgumentTypeError(
        f"Invalid YouTube URL: {url}\n"
        "Expected format: https://www.youtube.com/watch?v=VIDEO_ID"
    )


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Read YouTube live chat messages aloud using text-to-speech",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "https://www.youtube.com/watch?v=VIDEO_ID"
  %(prog)s URL --voice pico --rate 10
  %(prog)s URL --no-username --max-length 150

Controls (while running):
  p - Pause/Resume speech
  q - Quit application
        """,
    )

    parser.add_argument(
        "url", type=validate_youtube_url, help="YouTube live stream URL"
    )

    parser.add_argument(
        "--voice",
        choices=["espeak-ng", "pico", "festival"],
        default="espeak-ng",
        help="TTS voice engine (default: espeak-ng)",
    )

    parser.add_argument(
        "--rate",
        type=int,
        default=0,
        help="Speech rate from -100 (slow) to 100 (fast) (default: 0)",
    )

    parser.add_argument(
        "--volume",
        type=int,
        default=100,
        help="Volume from 0 to 100 (default: 100)",
    )

    parser.add_argument(
        "--pitch",
        type=int,
        default=0,
        help="Voice pitch from -100 (low) to 100 (high) (default: 0)",
    )

    parser.add_argument(
        "--max-length",
        type=int,
        default=200,
        help="Maximum message length to speak (default: 200)",
    )

    parser.add_argument(
        "--no-username",
        action="store_true",
        help="Skip reading usernames, only read message text",
    )

    parser.add_argument(
        "--language",
        default="en",
        help="TTS language code (default: en)",
    )

    parser.add_argument(
        "--queue-size",
        type=int,
        default=50,
        help="Maximum message queue size (default: 50)",
    )

    parser.add_argument(
        "--cookies",
        type=str,
        default=None,
        help="Path to cookies file (Netscape format) to bypass YouTube consent page",
    )

    return parser.parse_args()


def signal_handler(sig, frame, shutdown_event):
    """Handle Ctrl+C gracefully"""
    print("\n\nShutting down...")
    shutdown_event.set()


def main():
    """Main application entry point"""
    # Parse arguments
    args = parse_args()

    # Create configuration
    config = Config(
        youtube_url=args.url,
        voice_module=args.voice,
        speech_rate=args.rate,
        speech_volume=args.volume,
        speech_pitch=args.pitch,
        max_message_length=args.max_length,
        include_username=not args.no_username,
        language=args.language,
        queue_max_size=args.queue_size,
        cookies_path=args.cookies,
    )

    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    # Create shared state
    message_queue = queue.Queue(maxsize=config.queue_max_size)
    pause_event = threading.Event()
    pause_event.set()  # Start unpaused
    shutdown_event = threading.Event()

    # Setup signal handler for Ctrl+C
    signal.signal(
        signal.SIGINT, lambda sig, frame: signal_handler(sig, frame, shutdown_event)
    )

    # Create components
    chat_reader = ChatReader(config, message_queue, shutdown_event)
    tts_speaker = TTSSpeaker(config, message_queue, pause_event, shutdown_event)

    # Start threads
    print("\nYouTube Live Chat TTS Reader")
    print("=" * 50)
    print(f"Stream: {config.youtube_url}")
    print(f"Voice: {config.voice_module}")
    print("=" * 50)

    try:
        tts_speaker.start()
        chat_reader.start()

        print("\nControls:")
        print("  p - Pause/Resume")
        print("  q - Quit")
        print("-" * 50)
        print()

        # Main control loop
        while not shutdown_event.is_set():
            try:
                cmd = input().strip().lower()

                if cmd == "p":
                    if pause_event.is_set():
                        pause_event.clear()
                        print("⏸  PAUSED")
                    else:
                        pause_event.set()
                        print("▶  RESUMED")

                elif cmd == "q":
                    print("Quitting...")
                    shutdown_event.set()
                    break

                elif cmd == "":
                    # Allow empty input (just pressing Enter)
                    continue

                else:
                    print(f"Unknown command: {cmd}")
                    print("Use 'p' to pause/resume or 'q' to quit")

            except EOFError:
                # stdin closed
                break

    except Exception as e:
        print(f"Error: {e}")
        shutdown_event.set()

    finally:
        # Wait for threads to finish
        print("Waiting for threads to stop...")
        chat_reader.join(timeout=2)
        tts_speaker.join(timeout=2)
        print("Done")


if __name__ == "__main__":
    main()
