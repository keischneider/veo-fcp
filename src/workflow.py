"""
Main workflow orchestrator for video generation pipeline
"""
import os
import logging
from typing import Optional
from pathlib import Path

from src.clients.veo_client import VeoClient
from src.clients.tts_client import TTSClient
from src.clients.lipsync_client import LipSyncClient
from src.utils.video_processor import VideoProcessor
from src.utils.scene_manager import SceneManager
from src.models.prompt import VideoPrompt, SceneConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VideoProductionWorkflow:
    """
    Orchestrates the complete video production workflow:
    1. Generate video with Veo
    2. Download and convert to ProRes
    3. Generate TTS audio
    4. Apply lip-sync
    5. Convert final video to ProRes
    """

    def __init__(
        self,
        project_root: str = "./project",
        prores_profile: int = 2
    ):
        """
        Initialize workflow

        Args:
            project_root: Root directory for project
            prores_profile: ProRes profile (0=Proxy, 1=LT, 2=422, 3=422HQ)
        """
        self.project_root = project_root

        # Initialize clients
        self.veo_client = VeoClient()
        self.tts_client = TTSClient()
        self.lipsync_client = LipSyncClient()
        self.video_processor = VideoProcessor(prores_profile=prores_profile)
        self.scene_manager = SceneManager(project_root=project_root)

        logger.info("Initialized VideoProductionWorkflow")

    def process_scene(
        self,
        scene_config: SceneConfig,
        voice_id: Optional[str] = None,
        skip_lipsync: bool = False
    ) -> dict:
        """
        Process a complete scene through the pipeline

        Args:
            scene_config: Scene configuration with prompt
            voice_id: Optional voice ID for TTS
            skip_lipsync: Skip lip-sync step if True

        Returns:
            Dictionary with paths to generated files
        """
        scene_id = scene_config.scene_id
        prompt = scene_config.prompt

        logger.info(f"=== Processing {scene_id} ===")

        # Create scene folder
        scene_path = self.scene_manager.create_scene(scene_id)
        self.scene_manager.update_scene_status(scene_id, "generating_video")

        result = {
            "scene_id": scene_id,
            "scene_path": scene_path
        }

        try:
            # Step 1: Generate video with Veo
            logger.info(f"Step 1: Generating video with Veo")
            veo_prompt = prompt.to_veo_prompt()
            logger.info(f"Veo prompt: {veo_prompt}")

            job = self.veo_client.generate_video(prompt=veo_prompt)
            job_status = self.veo_client.wait_for_completion(job["job_id"])
            video_url = job_status.get("video_url")

            logger.info(f"Video generated: {video_url}")

            # Step 2: Download and convert to ProRes
            logger.info(f"Step 2: Downloading and converting to ProRes")
            self.scene_manager.update_scene_status(scene_id, "downloading")

            raw_video_path = os.path.join(scene_path, f"{scene_id}_veo_raw.mp4")
            self.video_processor.download_video(video_url, raw_video_path)

            prores_path = os.path.join(scene_path, f"{scene_id}_veo_prores.mov")
            self.video_processor.convert_to_prores(raw_video_path, prores_path)

            self.scene_manager.save_file_reference(scene_id, "raw_video", raw_video_path)
            self.scene_manager.save_file_reference(scene_id, "prores_video", prores_path)

            result["raw_video"] = raw_video_path
            result["prores_video"] = prores_path

            # Step 3: Generate TTS audio (if dialogue exists)
            dialogue = prompt.get_dialogue()

            if dialogue and dialogue.strip():
                logger.info(f"Step 3: Generating TTS audio")
                self.scene_manager.update_scene_status(scene_id, "generating_audio")

                audio_path = os.path.join(scene_path, f"{scene_id}_dialogue.wav")
                self.tts_client.generate_speech(
                    text=dialogue,
                    output_path=audio_path,
                    voice_id=voice_id
                )

                self.scene_manager.save_file_reference(scene_id, "audio", audio_path)
                result["audio"] = audio_path

                # Step 4: Apply lip-sync
                if not skip_lipsync:
                    logger.info(f"Step 4: Applying lip-sync")
                    self.scene_manager.update_scene_status(scene_id, "lip_syncing")

                    synced_path = os.path.join(scene_path, f"{scene_id}_synced.mp4")
                    self.lipsync_client.create_and_wait(
                        video_path=raw_video_path,
                        audio_path=audio_path,
                        output_path=synced_path
                    )

                    # Step 5: Convert synced video to ProRes
                    logger.info(f"Step 5: Converting synced video to ProRes")
                    final_prores_path = os.path.join(
                        scene_path,
                        f"{scene_id}_final_prores.mov"
                    )
                    self.video_processor.convert_to_prores(
                        synced_path,
                        final_prores_path
                    )

                    self.scene_manager.save_file_reference(
                        scene_id,
                        "synced_video",
                        synced_path
                    )
                    self.scene_manager.save_file_reference(
                        scene_id,
                        "final_prores",
                        final_prores_path
                    )

                    result["synced_video"] = synced_path
                    result["final_prores"] = final_prores_path
                else:
                    logger.info("Skipping lip-sync step")
                    result["final_prores"] = prores_path
            else:
                logger.info("No dialogue provided, skipping audio and lip-sync")
                result["final_prores"] = prores_path

            # Mark as completed
            self.scene_manager.update_scene_status(scene_id, "completed")
            logger.info(f"=== {scene_id} completed successfully ===")

            return result

        except Exception as e:
            logger.error(f"Error processing {scene_id}: {str(e)}")
            self.scene_manager.update_scene_status(scene_id, "failed")
            raise

    def process_multiple_scenes(
        self,
        scene_configs: list[SceneConfig],
        voice_id: Optional[str] = None,
        skip_lipsync: bool = False
    ) -> list[dict]:
        """
        Process multiple scenes

        Args:
            scene_configs: List of scene configurations
            voice_id: Optional voice ID for TTS
            skip_lipsync: Skip lip-sync step if True

        Returns:
            List of results for each scene
        """
        results = []

        for config in scene_configs:
            try:
                result = self.process_scene(
                    config,
                    voice_id=voice_id,
                    skip_lipsync=skip_lipsync
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {config.scene_id}: {str(e)}")
                results.append({
                    "scene_id": config.scene_id,
                    "error": str(e)
                })

        return results

    def get_project_status(self) -> dict:
        """
        Get status of all scenes in the project

        Returns:
            Dictionary with project status
        """
        return self.scene_manager.get_project_structure()
