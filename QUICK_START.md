# Quick Start Guide

Get up and running with VEO-FCP in 5 minutes!

## Step 1: Install (2 minutes)

```bash
# Navigate to project
cd veo-fcp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install FFmpeg (macOS)
brew install ffmpeg
```

## Step 2: Configure (2 minutes)

```bash
# Run setup wizard
python cli.py setup
```

You'll need:
- Google Cloud Project ID
- Path to Google service account JSON key
- ElevenLabs API key
- D-ID API key

## Step 3: Generate Your First Video (1 minute)

```bash
python cli.py generate \
  --scene-id test_scene \
  --prompt "A astronaut floating in space, looking at Earth" \
  --dialogue "Houston, the view from up here is incredible."
```

## Step 4: Import to Final Cut Pro

Find your video at:
```
project/scenes/test_scene/test_scene_final_prores.mov
```

Drag and drop into Final Cut Pro!

## What Just Happened?

The tool automatically:
1. ✓ Generated video from your text prompt using Google Veo
2. ✓ Downloaded the video
3. ✓ Converted to ProRes 422 format
4. ✓ Generated speech audio from your dialogue text
5. ✓ Applied AI lip-sync to match the dialogue
6. ✓ Converted final result to ProRes for FCP

## Next Steps

### Try Batch Processing

Create `my_scenes.json`:
```json
{
  "scenes": [
    {
      "scene_id": "scene_01",
      "prompt": {
        "cinematic_description": "Your scene description here",
        "dialogue_text": "Your dialogue here"
      }
    }
  ]
}
```

Run:
```bash
python cli.py batch --config-file my_scenes.json
```

### Check Project Status

```bash
python cli.py status
```

### Learn More

- [SETUP.md](SETUP.md) - Detailed setup instructions
- [USAGE.md](USAGE.md) - Complete usage guide
- [examples/](examples/) - Example scenes and scripts

## Common Commands

```bash
# Generate scene with all options
python cli.py generate \
  --scene-id scene_01 \
  --prompt "Visual description" \
  --character "Character details" \
  --camera "Camera movement" \
  --lighting "Lighting style" \
  --emotion "Emotional tone" \
  --dialogue "Spoken words"

# Skip lip-sync (faster, no dialogue sync)
python cli.py generate \
  --scene-id scene_02 \
  --prompt "Establishing shot of city" \
  --skip-lipsync

# Use custom voice
python cli.py generate \
  --scene-id scene_03 \
  --prompt "News anchor speaks" \
  --dialogue "Breaking news..." \
  --voice-id "pNInz6obpgDQGcFmaJgB"

# Check status
python cli.py status
```

## Troubleshooting

**Error: FFmpeg not found**
```bash
brew install ffmpeg  # macOS
```

**Error: API authentication failed**
- Check your API keys in `.env`
- Verify Google service account JSON path

**Error: Module not found**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Getting Help

- Read [USAGE.md](USAGE.md) for detailed documentation
- Check [examples/](examples/) for working examples
- Review error messages for specific issues

Ready to create amazing videos? Let's go!
