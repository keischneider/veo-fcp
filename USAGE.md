# VEO-FCP Usage Guide

## Overview

VEO-FCP is a complete video production pipeline that:

1. Generates videos using Google Veo API
2. Downloads and converts to Apple ProRes 422
3. Generates dialogue audio with ElevenLabs TTS
4. Applies lip-sync using D-ID
5. Outputs Final Cut Pro-ready ProRes files

## Workflow Diagram

```
Prompt → Veo API → MP4 → ProRes Conversion
                            ↓
                    (if dialogue exists)
                            ↓
Text → ElevenLabs TTS → Audio.wav
                            ↓
Video + Audio → D-ID Lip-sync → Synced MP4 → Final ProRes
```

## CLI Commands

### 1. Generate a Single Scene

```bash
python cli.py generate \
  --scene-id scene_01 \
  --prompt "A woman in her 30s walks through a futuristic city at sunset" \
  --character "Asian woman, short black hair, blue jacket" \
  --camera "Tracking shot, medium close-up" \
  --lighting "Golden hour, warm tones" \
  --emotion "Contemplative, slightly melancholic" \
  --dialogue "The city never sleeps, but sometimes I wish it would."
```

**Options:**
- `--scene-id`: Scene identifier (required)
- `--prompt`: Main cinematic description (required)
- `--character`: Character consistency notes
- `--camera`: Camera movement instructions
- `--lighting`: Lighting and style guidance
- `--emotion`: Emotional tone and performance
- `--dialogue`: Text for TTS and lip-sync
- `--voice-id`: Custom ElevenLabs voice ID
- `--skip-lipsync`: Skip lip-sync step
- `--project-root`: Custom project directory

### 2. Batch Process Multiple Scenes

Create a config file `scenes.json`:

```json
{
  "scenes": [
    {
      "scene_id": "scene_01",
      "prompt": {
        "cinematic_description": "A woman walks through a futuristic city",
        "character_consistency": "Asian woman, short black hair, blue jacket",
        "camera_movement": "Tracking shot, medium close-up",
        "lighting_style": "Golden hour, warm tones",
        "emotion_performance": "Contemplative",
        "dialogue_text": "The city never sleeps."
      }
    },
    {
      "scene_id": "scene_02",
      "prompt": {
        "cinematic_description": "Close-up of her face as she looks up",
        "character_consistency": "Same woman from scene 01",
        "camera_movement": "Static, slowly pushing in",
        "lighting_style": "Neon reflections on her face",
        "emotion_performance": "Hopeful, determined",
        "dialogue_text": "But I can make a difference."
      }
    }
  ]
}
```

Then run:

```bash
python cli.py batch --config-file scenes.json
```

### 3. Check Project Status

```bash
python cli.py status
```

Shows all scenes and their processing status.

### 4. Run Setup Wizard

```bash
python cli.py setup
```

Interactive setup for API credentials.

## Python API Usage

You can also use the workflow programmatically:

```python
from src.workflow import VideoProductionWorkflow
from src.models.prompt import VideoPrompt, SceneConfig

# Create a prompt
prompt = VideoPrompt(
    cinematic_description="A spaceship lands on an alien planet",
    character_consistency="Sleek silver spacecraft, blue engines",
    camera_movement="Wide establishing shot, slow zoom in",
    lighting_style="Dramatic backlit by twin suns",
    emotion_performance="Awe-inspiring, majestic",
    dialogue_text="We've arrived at our new home."
)

# Create scene config
config = SceneConfig(
    scene_id="scene_intro",
    prompt=prompt
)

# Initialize workflow
workflow = VideoProductionWorkflow(project_root="./project")

# Process scene
result = workflow.process_scene(config)

print(f"Final video: {result['final_prores']}")
```

## Output Structure

After processing, your project will look like:

```
project/
└── scenes/
    ├── scene_01/
    │   ├── metadata.json
    │   ├── scene_01_veo_raw.mp4
    │   ├── scene_01_veo_prores.mov
    │   ├── scene_01_dialogue.wav
    │   ├── scene_01_synced.mp4
    │   └── scene_01_final_prores.mov  ← Import this to FCP
    ├── scene_02/
    │   └── ...
    └── scene_03/
        └── ...
```

## Importing to Final Cut Pro

1. Open Final Cut Pro
2. Create a new library: `StoryProject.fcpbundle`
3. Create events:
   - `01_Scenes`
   - `02_Audio`
   - `03_Music`
   - `04_SFX`
   - `05_VFX`
4. Import the `*_final_prores.mov` files into `01_Scenes`
5. Create timeline projects for each scene
6. Edit and export

## Voice Selection

List available ElevenLabs voices:

```python
from src.clients.tts_client import TTSClient

client = TTSClient()
voices = client.list_voices()

for voice in voices:
    print(f"{voice.name}: {voice.voice_id}")
```

Use a specific voice:

```bash
python cli.py generate \
  --scene-id scene_01 \
  --prompt "..." \
  --dialogue "..." \
  --voice-id "pNInz6obpgDQGcFmaJgB"  # Adam voice
```

## Tips and Best Practices

### 1. Prompt Engineering

**Good prompts:**
- Be specific about visual details
- Include camera movement for dynamic shots
- Specify lighting for mood consistency
- Describe character appearance for consistency

**Example:**
```
"Wide shot of a detective's office at night. Rain streaks down the
window behind a tired-looking man in his 40s, grey suit, stubble.
Camera slowly dollies in while he reviews case files under a single
desk lamp. Film noir aesthetic, high contrast, venetian blind shadows."
```

### 2. Character Consistency

For multiple scenes with the same character:
- Keep character descriptions identical
- Reference previous scenes: "Same woman from scene 01"
- Mention specific identifiable features

### 3. Dialogue Optimization

- Keep dialogue concise
- Match dialogue to video pacing
- Consider lip-sync limitations
- Use natural speech patterns

### 4. ProRes Profiles

Choose based on your needs:
- **0 (Proxy)**: Lightweight, for editing on less powerful machines
- **1 (LT)**: Good balance for most editing
- **2 (422)**: Standard broadcast quality (default)
- **3 (422 HQ)**: High quality for color grading

Set in `.env`:
```
FFMPEG_PRORES_PROFILE=2
```

### 5. Skip Lip-sync for Non-dialogue Scenes

Save time and costs:

```bash
python cli.py generate \
  --scene-id scene_establishing \
  --prompt "Wide aerial shot of city skyline" \
  --skip-lipsync
```

## Troubleshooting

### FFmpeg not found
```bash
# macOS
brew install ffmpeg

# Verify
ffmpeg -version
```

### Google Cloud authentication error
```bash
# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

### ElevenLabs quota exceeded
- Check your plan limits
- Consider upgrading or waiting for quota reset

### D-ID processing timeout
- Increase timeout in code
- Check video file size (D-ID has limits)
- Verify API key is valid

## Advanced Usage

### Custom Video Processing

```python
from src.utils.video_processor import VideoProcessor

processor = VideoProcessor(prores_profile=3)  # 422 HQ

# Download video
processor.download_video(url, "output.mp4")

# Convert to ProRes
processor.convert_to_prores("output.mp4", "output_prores.mov")

# Get video info
info = processor.get_video_info("output.mp4")
print(f"Duration: {info['duration']}s, Resolution: {info['width']}x{info['height']}")
```

### Scene Management

```python
from src.utils.scene_manager import SceneManager

manager = SceneManager(project_root="./project")

# Create scene
scene_path = manager.create_scene("scene_05")

# Save file references
manager.save_file_reference("scene_05", "raw_video", "/path/to/video.mp4")

# Update status
manager.update_scene_status("scene_05", "completed")

# List all scenes
scenes = manager.list_scenes()
print(scenes)  # ['scene_01', 'scene_02', 'scene_05']
```

## Support

For issues or questions:
1. Check this documentation
2. Review error messages in console
3. Verify API credentials and quotas
4. Check API service status pages
