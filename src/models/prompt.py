"""
Prompt models for video generation
"""
from pydantic import BaseModel, Field
from typing import Optional


class VideoPrompt(BaseModel):
    """Structured video generation prompt"""

    cinematic_description: str = Field(
        ...,
        description="Main visual description of the scene"
    )
    character_consistency: Optional[str] = Field(
        None,
        description="Character appearance and consistency notes"
    )
    camera_movement: Optional[str] = Field(
        None,
        description="Camera movement and framing instructions"
    )
    lighting_style: Optional[str] = Field(
        None,
        description="Lighting and visual style guidance"
    )
    emotion_performance: Optional[str] = Field(
        None,
        description="Emotional tone and facial performance notes"
    )
    dialogue_text: Optional[str] = Field(
        None,
        description="Dialogue text for TTS and lip-sync"
    )

    def to_veo_prompt(self) -> str:
        """Convert structured prompt to single string for Veo API"""
        parts = [self.cinematic_description]

        if self.character_consistency:
            parts.append(f"Character: {self.character_consistency}")
        if self.camera_movement:
            parts.append(f"Camera: {self.camera_movement}")
        if self.lighting_style:
            parts.append(f"Lighting: {self.lighting_style}")
        if self.emotion_performance:
            parts.append(f"Performance: {self.emotion_performance}")

        return ". ".join(parts)

    def get_dialogue(self) -> str:
        """Get dialogue text for TTS"""
        return self.dialogue_text or ""


class SceneConfig(BaseModel):
    """Configuration for a scene"""

    scene_id: str = Field(..., description="Scene identifier (e.g., scene_01)")
    prompt: VideoPrompt
    output_dir: Optional[str] = Field(None, description="Custom output directory")
