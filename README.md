# VEO-FCP: AI Video Generation Pipeline for Final Cut Pro

Complete automated pipeline for generating cinematic videos with dialogue using Google Veo, ElevenLabs TTS, and D-ID lip-sync, optimized for Final Cut Pro workflows.

## Features

- **Google Veo API Integration**: Generate high-quality videos from text prompts
- **Automatic ProRes Conversion**: Converts all videos to Apple ProRes 422 for seamless FCP import
- **Text-to-Speech**: ElevenLabs integration for natural-sounding dialogue
- **AI Lip-Sync**: D-ID Creative Reality Studio for realistic lip-syncing
- **Scene Management**: Organized folder structure for multi-scene projects
- **Batch Processing**: Process multiple scenes from JSON config files
- **CLI Interface**: Easy-to-use command-line interface
- **Python API**: Use programmatically in your own scripts

## Workflow

```
Text Prompt → Veo API → Video (MP4)
                ↓
        Download & Convert → ProRes 422
                ↓
    (if dialogue exists)
                ↓
        Text → ElevenLabs TTS → Audio (WAV)
                ↓
    Video + Audio → D-ID Lip-sync → Synced Video
                ↓
        Convert to ProRes 422 → Final Cut Pro Ready
```

## Quick Start

### 1. Installation

```bash
# Clone or navigate to the project
cd veo-fcp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install FFmpeg (macOS)
brew install ffmpeg
```

### 2. Configure API Keys

```bash
# Run setup wizard
python cli.py setup

# Or manually copy .env.example to .env and edit
cp .env.example .env
```

### 3. Generate Your First Scene

```bash
python cli.py generate \
  --scene-id scene_01 \
  --prompt "A woman walks through a futuristic city at sunset" \
  --dialogue "The city never sleeps, but sometimes I wish it would."
```

### 4. Import to Final Cut Pro

The final ProRes video will be saved to:
```
project/scenes/scene_01/scene_01_final_prores.mov
```

Import this file directly into Final Cut Pro!

## Documentation

- [SETUP.md](SETUP.md) - Detailed installation and configuration guide
- [USAGE.md](USAGE.md) - Complete usage documentation and examples
- [examples/](examples/) - Example scene configuration files

## Project Structure

```
veo-fcp/
├── src/
│   ├── clients/
│   │   ├── veo_client.py       # Google Veo API client
│   │   ├── tts_client.py       # ElevenLabs TTS client
│   │   └── lipsync_client.py   # D-ID lip-sync client
│   ├── utils/
│   │   ├── video_processor.py  # Video download & ProRes conversion
│   │   └── scene_manager.py    # Scene folder management
│   ├── models/
│   │   └── prompt.py           # Prompt data models
│   └── workflow.py             # Main workflow orchestrator
├── cli.py                      # Command-line interface
├── examples/                   # Example configuration files
└── project/
    └── scenes/                 # Generated scenes output
        ├── scene_01/
        ├── scene_02/
        └── scene_03/
```

## CLI Commands

### Generate Single Scene
```bash
python cli.py generate \
  --scene-id scene_01 \
  --prompt "Your cinematic description" \
  --character "Character details" \
  --camera "Camera movement" \
  --lighting "Lighting style" \
  --emotion "Emotional tone" \
  --dialogue "Spoken dialogue"
```

### Batch Process Multiple Scenes
```bash
python cli.py batch --config-file examples/multi_scene_story.json
```

### Check Project Status
```bash
python cli.py status
```

## Final Cut Pro Integration

### Inside FCP create:

#### Libraries
- StoryProject.fcpbundle

#### Events
- 01_Scenes
- 02_Audio
- 03_Music
- 04_SFX
- 05_VFX

#### Projects
- Scene_01
- Scene_02
- Scene_03
- Final_Master

### Workflow in FCP:

1. Import ProRes scene clips from `project/scenes/*/`
2. Lay in synced dialogue
3. Add background ambience per scene
4. Add sound design
5. Insert transitions or match cuts between scenes
6. Final color correction + grading
7. Export in ProRes 422 or H.264

## Requirements

- Python 3.9+
- FFmpeg
- Google Cloud account with Veo API access
- ElevenLabs API key
- D-ID API key

## API Providers

- **Google Veo**: https://cloud.google.com/vertex-ai/docs
- **ElevenLabs**: https://elevenlabs.io/
- **D-ID**: https://www.d-id.com/

## Example Output

After processing, each scene folder contains:

```
scene_01/
├── metadata.json                    # Scene metadata
├── scene_01_veo_raw.mp4            # Raw Veo output
├── scene_01_veo_prores.mov         # ProRes conversion
├── scene_01_dialogue.wav           # Generated TTS audio
├── scene_01_synced.mp4             # Lip-synced video
└── scene_01_final_prores.mov       # Final FCP-ready file ✓
```

## Advanced Usage

### Python API

```python
from src.workflow import VideoProductionWorkflow
from src.models.prompt import VideoPrompt, SceneConfig

# Create workflow
workflow = VideoProductionWorkflow(project_root="./project")

# Define prompt
prompt = VideoPrompt(
    cinematic_description="A spaceship lands on Mars",
    camera_movement="Wide establishing shot",
    lighting_style="Dramatic sunset lighting",
    dialogue_text="We've arrived at our destination."
)

# Process scene
config = SceneConfig(scene_id="scene_mars", prompt=prompt)
result = workflow.process_scene(config)

print(f"Final video: {result['final_prores']}")
```

## Troubleshooting

### Common Issues

1. **FFmpeg not found**: Install FFmpeg and ensure it's in your PATH
2. **API authentication errors**: Verify your API keys in `.env`
3. **Quota exceeded**: Check your API plan limits
4. **Video processing timeout**: Increase timeout values for longer videos

See [USAGE.md](USAGE.md) for detailed troubleshooting.

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

## Support

For questions or issues, please open a GitHub issue.
