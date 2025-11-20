"""YouTube chat reader thread"""

import queue
import re
import threading
from typing import Optional

from chat_downloader import ChatDownloader

from .config import Config


class ChatReader:
    """Reads YouTube live chat messages and queues them for TTS"""

    def __init__(
        self,
        config: Config,
        message_queue: queue.Queue,
        shutdown_event: threading.Event,
    ):
        self.config = config
        self.message_queue = message_queue
        self.shutdown_event = shutdown_event
        self.thread: Optional[threading.Thread] = None

    def _format_message(self, message: dict) -> Optional[str]:
        """Format a chat message for TTS

        Args:
            message: Message dictionary from chat-downloader

        Returns:
            Formatted message string, or None if message should be skipped
        """
        # Only process text messages
        if message.get("message_type") != "text_message":
            return None

        author = message.get("author", {}).get("name", "Unknown")
        text = message.get("message", "")

        if not text:
            return None

        # Truncate long messages
        if len(text) > self.config.max_message_length:
            text = text[: self.config.max_message_length] + "..."

        # Remove URLs (replace with placeholder)
        text = re.sub(r"http\S+", "[link]", text)

        # Format with or without username
        if self.config.include_username:
            return f"{author} says: {text}"
        else:
            return text

    def _run(self):
        """Main chat reader loop"""
        try:
            print(f"Connecting to YouTube chat: {self.config.youtube_url}")

            # Create ChatDownloader with cookies if provided
            downloader_params = {}
            if self.config.cookies_path:
                print(f"Using cookies from: {self.config.cookies_path}")
                downloader_params['cookies'] = self.config.cookies_path

            downloader = ChatDownloader(**downloader_params)

            # Try to get chat with additional error information
            try:
                chat = downloader.get_chat(
                    self.config.youtube_url,
                    message_groups=['messages', 'superchat'],
                )
                print("Connected to YouTube chat successfully")
            except ValueError as e:
                error_msg = str(e).lower()
                if "unable to parse" in error_msg:
                    print("\nError: Unable to parse video data.")
                    if not self.config.cookies_path:
                        print("\n⚠️  This is often caused by YouTube's cookie consent page.")
                        print("Solution: Export cookies from your browser and use --cookies")
                        print("\nSteps to fix:")
                        print("  1. Install a browser extension like 'Get cookies.txt LOCALLY'")
                        print("  2. Visit youtube.com and accept cookies")
                        print("  3. Export cookies to a file (cookies.txt)")
                        print("  4. Run: yt-liveread URL --cookies cookies.txt")
                    else:
                        print("\n⚠️  Cookie file was provided but parsing still failed.")
                        print("Possible reasons:")
                        print("  - The stream might not be live yet (check if it's 'upcoming')")
                        print("  - The stream might have ended")
                        print("  - Chat might be disabled for this stream")
                        print("  - The cookies might be expired or invalid")
                    print("\nTip: Make sure you're using a currently LIVE stream with chat enabled")
                elif "no messages" in error_msg or "chat" in error_msg:
                    print("\nError: This stream does not have chat available")
                    print("  - Chat might be disabled by the streamer")
                    print("  - The video might not be a livestream")
                else:
                    print(f"\nError connecting to chat: {e}")
                self.shutdown_event.set()
                return
            except Exception as e:
                print(f"\nUnexpected error connecting to chat: {e}")
                print("Please check that the URL is correct and the stream is live")
                self.shutdown_event.set()
                return

            # Read messages from chat
            message_count = 0
            for message in chat:
                # Check for shutdown
                if self.shutdown_event.is_set():
                    break

                # Format and queue message
                formatted = self._format_message(message)
                if formatted:
                    try:
                        # Try to put in queue, skip if full
                        self.message_queue.put(formatted, timeout=0.1)
                        message_count += 1

                        # Print first message as confirmation
                        if message_count == 1:
                            print(f"Receiving messages... (first message received)")

                    except queue.Full:
                        # Queue is full, skip this message
                        pass

            if message_count == 0:
                print("\nNo messages received. The chat might be very quiet or disabled.")

        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"\nChat reader error: {e}")
            print("Chat reader stopped due to error")
            import traceback
            traceback.print_exc()
        finally:
            print("Chat reader thread stopped")

    def start(self):
        """Start the chat reader thread"""
        if self.thread is not None and self.thread.is_alive():
            raise RuntimeError("Chat reader thread is already running")

        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def join(self, timeout: Optional[float] = None):
        """Wait for the chat reader thread to finish"""
        if self.thread is not None:
            self.thread.join(timeout=timeout)
