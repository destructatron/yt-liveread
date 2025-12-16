"""Text-to-speech speaker thread using Speech Dispatcher"""

import queue
import sys
import threading
from typing import Optional

try:
    import speechd
except ImportError:
    print("ERROR: python3-speechd is not installed")
    print("Install with: sudo apt install python3-speechd speech-dispatcher")
    sys.exit(1)

from .config import Config


class TTSSpeaker:
    """Speaks messages using Speech Dispatcher"""

    def __init__(
        self,
        config: Config,
        message_queue: queue.Queue,
        pause_event: threading.Event,
        shutdown_event: threading.Event,
    ):
        self.config = config
        self.message_queue = message_queue
        self.pause_event = pause_event
        self.shutdown_event = shutdown_event
        self.thread: Optional[threading.Thread] = None
        self.client: Optional[speechd.SSIPClient] = None
        self.ready_event = threading.Event()  # Set when TTS is ready to receive messages

    def _setup_client(self):
        """Initialize and configure Speech Dispatcher client"""
        try:
            self.client = speechd.SSIPClient("yt-liveread")

            # Configure voice settings
            self.client.set_output_module(self.config.voice_module)
            self.client.set_language(self.config.language)
            self.client.set_rate(self.config.speech_rate)
            self.client.set_volume(self.config.speech_volume)
            self.client.set_pitch(self.config.speech_pitch)

            # Set priority to TEXT (low) so screen readers like Orca can interrupt
            self.client.set_priority(speechd.Priority.TEXT)

            print(
                f"Speech Dispatcher initialized (module: {self.config.voice_module}, priority: TEXT)"
            )
            return True

        except Exception as e:
            print(f"Failed to initialize Speech Dispatcher: {e}")
            print("Make sure speech-dispatcher is installed and running:")
            print("  sudo apt install speech-dispatcher python3-speechd")
            print("  systemctl --user status speech-dispatcher")
            return False

    def _run(self):
        """Main TTS speaker loop"""
        if not self._setup_client():
            self.ready_event.set()  # Signal ready even on failure so main doesn't block forever
            return

        # Signal that TTS is ready to receive messages
        self.ready_event.set()

        try:
            while not self.shutdown_event.is_set():
                try:
                    # Get message from queue with timeout
                    # Timeout allows us to check shutdown_event periodically
                    text = self.message_queue.get(timeout=0.5)

                    try:
                        # Wait if paused, checking shutdown periodically to avoid
                        # blocking indefinitely if shutdown is triggered while paused
                        while not self.pause_event.wait(timeout=0.5):
                            if self.shutdown_event.is_set():
                                break

                        # Check shutdown again after potentially waiting on pause
                        if self.shutdown_event.is_set():
                            break

                        # Print message to console
                        print(text)

                        # Speak the message
                        if self.client:
                            self.client.speak(text)

                    finally:
                        # Always mark task as done, even if an error occurred
                        self.message_queue.task_done()

                except queue.Empty:
                    # No messages, continue loop
                    continue
                except Exception as e:
                    print(f"Error speaking message: {e}")
                    # Continue despite errors with individual messages

        except Exception as e:
            print(f"TTS speaker error: {e}")
        finally:
            # Cleanup
            if self.client:
                try:
                    self.client.cancel()
                    self.client.close()
                except Exception as e:
                    print(f"Warning: Error closing Speech Dispatcher client: {e}")
            print("TTS speaker thread stopped")

    def start(self):
        """Start the TTS speaker thread"""
        if self.thread is not None and self.thread.is_alive():
            raise RuntimeError("TTS speaker thread is already running")

        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def cancel(self):
        """Cancel any currently playing or queued speech"""
        if self.client:
            try:
                self.client.cancel()
            except Exception:
                pass  # Ignore errors during cancellation

    def join(self, timeout: Optional[float] = None):
        """Wait for the TTS speaker thread to finish"""
        if self.thread is not None:
            self.thread.join(timeout=timeout)
