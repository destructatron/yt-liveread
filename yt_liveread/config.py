"""Configuration for YouTube Live Chat TTS Reader"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Application configuration"""

    # YouTube chat settings
    youtube_url: str
    max_message_length: int = 200
    cookies_path: Optional[str] = None

    # Speech Dispatcher settings
    voice_module: str = "espeak-ng"
    speech_rate: int = 0  # -100 to 100
    speech_volume: int = 100  # 0 to 100
    speech_pitch: int = 0  # -100 to 100
    language: str = "en"

    # Message formatting
    include_username: bool = True

    # Queue settings
    queue_max_size: int = 50

    def validate(self) -> None:
        """Validate configuration values"""
        if not self.youtube_url:
            raise ValueError("YouTube URL is required")

        if not (-100 <= self.speech_rate <= 100):
            raise ValueError("Speech rate must be between -100 and 100")

        if not (0 <= self.speech_volume <= 100):
            raise ValueError("Speech volume must be between 0 and 100")

        if not (-100 <= self.speech_pitch <= 100):
            raise ValueError("Speech pitch must be between -100 and 100")

        if self.max_message_length < 1:
            raise ValueError("Max message length must be positive")

        if self.queue_max_size < 1:
            raise ValueError("Queue max size must be positive")
