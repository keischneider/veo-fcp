"""
Text-to-Speech API client using ElevenLabs
"""
import os
import logging
from typing import Optional
from elevenlabs.client import ElevenLabs
from elevenlabs import save

logger = logging.getLogger(__name__)


class TTSClient:
    """Client for ElevenLabs Text-to-Speech API"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_voice_id: Optional[str] = None
    ):
        """
        Initialize TTS client

        Args:
            api_key: ElevenLabs API key
            default_voice_id: Default voice ID to use
        """
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.default_voice_id = default_voice_id or os.getenv(
            "ELEVENLABS_VOICE_ID",
            "21m00Tcm4TlvDq8ikWAM"  # Default: Rachel voice
        )

        if not self.api_key:
            raise ValueError("ElevenLabs API key is required")

        self.client = ElevenLabs(api_key=self.api_key)
        logger.info("Initialized ElevenLabs TTS client")

    def generate_speech(
        self,
        text: str,
        output_path: str,
        voice_id: Optional[str] = None,
        model: str = "eleven_multilingual_v2",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        optimize_streaming_latency: int = 0
    ) -> str:
        """
        Generate speech from text

        Args:
            text: Text to convert to speech
            output_path: Path to save audio file
            voice_id: Voice ID (uses default if not provided)
            model: TTS model to use
            stability: Voice stability (0-1)
            similarity_boost: Voice similarity boost (0-1)
            optimize_streaming_latency: Latency optimization (0-4)

        Returns:
            Path to generated audio file
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        voice_id = voice_id or self.default_voice_id
        logger.info(f"Generating speech for text: {text[:50]}...")

        try:
            # Create output directory if needed
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Generate audio
            audio = self.client.generate(
                text=text,
                voice=voice_id,
                model=model,
                voice_settings={
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                }
            )

            # Save to file
            save(audio, output_path)

            logger.info(f"Generated speech saved to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error generating speech: {str(e)}")
            raise

    def list_voices(self) -> list:
        """
        List available voices

        Returns:
            List of available voices
        """
        try:
            voices = self.client.voices.get_all()
            return voices.voices
        except Exception as e:
            logger.error(f"Error listing voices: {str(e)}")
            raise

    def get_voice_info(self, voice_id: str) -> dict:
        """
        Get information about a specific voice

        Args:
            voice_id: Voice identifier

        Returns:
            Voice information dictionary
        """
        try:
            voice = self.client.voices.get(voice_id)
            return {
                "voice_id": voice.voice_id,
                "name": voice.name,
                "category": voice.category,
                "description": voice.description if hasattr(voice, 'description') else None,
            }
        except Exception as e:
            logger.error(f"Error getting voice info: {str(e)}")
            raise
