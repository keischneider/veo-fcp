"""
Scene management and folder structure handling
"""
import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class SceneManager:
    """Manages scene folders and metadata"""

    def __init__(self, project_root: str = "./project"):
        """
        Initialize scene manager

        Args:
            project_root: Root directory for the project
        """
        self.project_root = Path(project_root)
        self.scenes_dir = self.project_root / "scenes"

        # Create base directories
        self.scenes_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized SceneManager at {self.project_root}")

    def create_scene(self, scene_id: str) -> str:
        """
        Create a new scene folder

        Args:
            scene_id: Scene identifier (e.g., scene_01)

        Returns:
            Path to created scene directory
        """
        scene_path = self.scenes_dir / scene_id
        scene_path.mkdir(parents=True, exist_ok=True)

        # Create metadata file
        metadata_path = scene_path / "metadata.json"
        if not metadata_path.exists():
            metadata = {
                "scene_id": scene_id,
                "created_at": None,
                "status": "created",
                "files": {}
            }
            self._save_metadata(scene_id, metadata)

        logger.info(f"Created scene folder: {scene_path}")
        return str(scene_path)

    def get_scene_path(self, scene_id: str) -> str:
        """
        Get path to scene directory

        Args:
            scene_id: Scene identifier

        Returns:
            Path to scene directory
        """
        return str(self.scenes_dir / scene_id)

    def save_file_reference(
        self,
        scene_id: str,
        file_type: str,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Save reference to a file in scene metadata

        Args:
            scene_id: Scene identifier
            file_type: Type of file (e.g., 'raw_video', 'prores', 'audio', 'synced')
            file_path: Path to the file
            metadata: Additional metadata for the file
        """
        scene_metadata = self._load_metadata(scene_id)

        scene_metadata["files"][file_type] = {
            "path": file_path,
            "metadata": metadata or {}
        }

        self._save_metadata(scene_id, scene_metadata)
        logger.info(f"Saved {file_type} reference for {scene_id}: {file_path}")

    def get_file_path(self, scene_id: str, file_type: str) -> Optional[str]:
        """
        Get path to a specific file type in scene

        Args:
            scene_id: Scene identifier
            file_type: Type of file

        Returns:
            Path to file or None if not found
        """
        scene_metadata = self._load_metadata(scene_id)
        file_info = scene_metadata.get("files", {}).get(file_type)

        return file_info.get("path") if file_info else None

    def update_scene_status(self, scene_id: str, status: str):
        """
        Update scene processing status

        Args:
            scene_id: Scene identifier
            status: New status (e.g., 'generating', 'processing', 'completed')
        """
        scene_metadata = self._load_metadata(scene_id)
        scene_metadata["status"] = status
        self._save_metadata(scene_id, scene_metadata)

        logger.info(f"Updated {scene_id} status to: {status}")

    def get_scene_metadata(self, scene_id: str) -> Dict[str, Any]:
        """
        Get complete scene metadata

        Args:
            scene_id: Scene identifier

        Returns:
            Scene metadata dictionary
        """
        return self._load_metadata(scene_id)

    def list_scenes(self) -> list[str]:
        """
        List all scene IDs

        Returns:
            List of scene identifiers
        """
        scenes = []
        if self.scenes_dir.exists():
            for item in self.scenes_dir.iterdir():
                if item.is_dir():
                    scenes.append(item.name)

        return sorted(scenes)

    def get_project_structure(self) -> Dict[str, Any]:
        """
        Get complete project structure overview

        Returns:
            Dictionary with project structure information
        """
        structure = {
            "project_root": str(self.project_root),
            "scenes_dir": str(self.scenes_dir),
            "scenes": {}
        }

        for scene_id in self.list_scenes():
            metadata = self.get_scene_metadata(scene_id)
            structure["scenes"][scene_id] = {
                "status": metadata.get("status"),
                "files": list(metadata.get("files", {}).keys())
            }

        return structure

    def _load_metadata(self, scene_id: str) -> Dict[str, Any]:
        """Load scene metadata from JSON file"""
        metadata_path = self.scenes_dir / scene_id / "metadata.json"

        if not metadata_path.exists():
            return {
                "scene_id": scene_id,
                "status": "unknown",
                "files": {}
            }

        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading metadata for {scene_id}: {str(e)}")
            return {"scene_id": scene_id, "status": "error", "files": {}}

    def _save_metadata(self, scene_id: str, metadata: Dict[str, Any]):
        """Save scene metadata to JSON file"""
        metadata_path = self.scenes_dir / scene_id / "metadata.json"

        try:
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            with open(metadata_path, 'w') as f:
                json.dump(metadata, indent=2, fp=f)
        except Exception as e:
            logger.error(f"Error saving metadata for {scene_id}: {str(e)}")
            raise
