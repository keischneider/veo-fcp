#!/usr/bin/env python3
"""
CLI interface for VEO-FCP video generation pipeline
"""
import os
import sys
import json
import click
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.workflow import VideoProductionWorkflow
from src.models.prompt import VideoPrompt, SceneConfig

# Load environment variables
load_dotenv()

console = Console()


@click.group()
def cli():
    """VEO-FCP: Video Generation Pipeline for Final Cut Pro"""
    pass


@cli.command()
@click.option('--scene-id', required=True, help='Scene identifier (e.g., scene_01)')
@click.option('--prompt', required=True, help='Cinematic description')
@click.option('--character', help='Character consistency notes')
@click.option('--camera', help='Camera movement')
@click.option('--lighting', help='Lighting and style')
@click.option('--emotion', help='Emotion and facial performance')
@click.option('--dialogue', help='Dialogue text for TTS and lip-sync')
@click.option('--voice-id', help='ElevenLabs voice ID')
@click.option('--skip-lipsync', is_flag=True, help='Skip lip-sync step')
@click.option('--project-root', default='./project', help='Project root directory')
def generate(scene_id, prompt, character, camera, lighting, emotion, dialogue,
             voice_id, skip_lipsync, project_root):
    """Generate a video scene with optional TTS and lip-sync"""

    console.print(f"\n[bold cyan]VEO-FCP Video Generation Pipeline[/bold cyan]")
    console.print(f"Scene: [yellow]{scene_id}[/yellow]\n")

    # Create video prompt
    video_prompt = VideoPrompt(
        cinematic_description=prompt,
        character_consistency=character,
        camera_movement=camera,
        lighting_style=lighting,
        emotion_performance=emotion,
        dialogue_text=dialogue
    )

    # Create scene config
    scene_config = SceneConfig(
        scene_id=scene_id,
        prompt=video_prompt
    )

    # Initialize workflow
    workflow = VideoProductionWorkflow(project_root=project_root)

    # Process scene
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Processing scene...", total=None)

            result = workflow.process_scene(
                scene_config,
                voice_id=voice_id,
                skip_lipsync=skip_lipsync
            )

        # Display results
        console.print("\n[bold green]✓ Scene generated successfully![/bold green]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("File Type", style="cyan")
        table.add_column("Path", style="yellow")

        for key, value in result.items():
            if key not in ['scene_id', 'scene_path'] and value:
                table.add_row(key.replace('_', ' ').title(), value)

        console.print(table)
        console.print(f"\nFinal ProRes video: [green]{result.get('final_prores')}[/green]\n")

    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {str(e)}\n")
        sys.exit(1)


@cli.command()
@click.option('--config-file', required=True, type=click.Path(exists=True),
              help='JSON config file with scene definitions')
@click.option('--voice-id', help='ElevenLabs voice ID')
@click.option('--skip-lipsync', is_flag=True, help='Skip lip-sync step')
@click.option('--project-root', default='./project', help='Project root directory')
def batch(config_file, voice_id, skip_lipsync, project_root):
    """Process multiple scenes from a config file"""

    console.print(f"\n[bold cyan]VEO-FCP Batch Processing[/bold cyan]\n")

    # Load config file
    with open(config_file, 'r') as f:
        config_data = json.load(f)

    scenes = config_data.get('scenes', [])
    console.print(f"Processing {len(scenes)} scenes...\n")

    # Create scene configs
    scene_configs = []
    for scene_data in scenes:
        video_prompt = VideoPrompt(**scene_data['prompt'])
        scene_config = SceneConfig(
            scene_id=scene_data['scene_id'],
            prompt=video_prompt
        )
        scene_configs.append(scene_config)

    # Initialize workflow
    workflow = VideoProductionWorkflow(project_root=project_root)

    # Process scenes
    try:
        results = workflow.process_multiple_scenes(
            scene_configs,
            voice_id=voice_id,
            skip_lipsync=skip_lipsync
        )

        # Display results
        console.print("\n[bold green]Batch processing complete![/bold green]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Scene ID", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Final ProRes", style="green")

        for result in results:
            scene_id = result.get('scene_id', 'Unknown')
            if 'error' in result:
                table.add_row(scene_id, "[red]Failed[/red]", result['error'])
            else:
                table.add_row(
                    scene_id,
                    "[green]Success[/green]",
                    result.get('final_prores', 'N/A')
                )

        console.print(table)
        console.print()

    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {str(e)}\n")
        sys.exit(1)


@cli.command()
@click.option('--project-root', default='./project', help='Project root directory')
def status(project_root):
    """Show project status"""

    workflow = VideoProductionWorkflow(project_root=project_root)
    project_status = workflow.get_project_status()

    console.print(f"\n[bold cyan]Project Status[/bold cyan]")
    console.print(f"Root: [yellow]{project_status['project_root']}[/yellow]\n")

    if not project_status['scenes']:
        console.print("[yellow]No scenes found[/yellow]\n")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Scene ID", style="cyan")
    table.add_column("Status", style="yellow")
    table.add_column("Files", style="green")

    for scene_id, scene_info in project_status['scenes'].items():
        status_color = {
            'completed': 'green',
            'failed': 'red',
            'generating_video': 'yellow',
            'downloading': 'yellow',
            'generating_audio': 'yellow',
            'lip_syncing': 'yellow',
        }.get(scene_info['status'], 'white')

        table.add_row(
            scene_id,
            f"[{status_color}]{scene_info['status']}[/{status_color}]",
            ", ".join(scene_info['files'])
        )

    console.print(table)
    console.print()


@cli.command()
def setup():
    """Setup wizard for configuration"""

    console.print("\n[bold cyan]VEO-FCP Setup Wizard[/bold cyan]\n")

    # Check if .env exists
    env_path = Path('.env')
    if env_path.exists():
        console.print("[yellow].env file already exists[/yellow]")
        if not click.confirm("Overwrite?"):
            return

    console.print("Please provide your API credentials:\n")

    # Collect credentials
    google_project = click.prompt("Google Cloud Project ID")
    google_creds = click.prompt("Path to Google service account JSON")
    elevenlabs_key = click.prompt("ElevenLabs API Key")
    did_key = click.prompt("D-ID API Key")

    # Write .env file
    env_content = f"""# Google Cloud Configuration for Veo API
GOOGLE_CLOUD_PROJECT={google_project}
GOOGLE_APPLICATION_CREDENTIALS={google_creds}
VEO_LOCATION=us-central1

# ElevenLabs TTS API
ELEVENLABS_API_KEY={elevenlabs_key}
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# D-ID Lip Sync API
DID_API_KEY={did_key}

# Project Configuration
PROJECT_ROOT=./project
SCENES_DIR=./project/scenes

# FFmpeg Configuration
FFMPEG_PRORES_PROFILE=2
"""

    with open('.env', 'w') as f:
        f.write(env_content)

    console.print("\n[bold green]✓ Configuration saved to .env[/bold green]")
    console.print("\nYou can now start using VEO-FCP!\n")


if __name__ == '__main__':
    cli()
