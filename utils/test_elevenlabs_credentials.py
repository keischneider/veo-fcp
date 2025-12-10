#!/usr/bin/env python3
"""
Test ElevenLabs API credentials in isolation
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Get the project root directory (parent of utils/)
PROJECT_ROOT = Path(__file__).parent.parent

# Load environment variables from project root
load_dotenv(PROJECT_ROOT / ".env")


def test_elevenlabs_credentials():
    """Test ElevenLabs API credentials"""

    print("=" * 60)
    print("ElevenLabs API Credentials Test")
    print("=" * 60)
    print()

    # Step 1: Check environment variables
    print("Step 1: Checking environment variables...")

    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID")

    print(f"  ELEVENLABS_API_KEY: {'*' * 20 if api_key else '[NOT SET]'}")
    print(f"  ELEVENLABS_VOICE_ID: {voice_id or '[NOT SET]'}")
    print()

    if not api_key:
        print("❌ ERROR: ELEVENLABS_API_KEY is not set in .env")
        print("   Add: ELEVENLABS_API_KEY=your-api-key")
        print()
        print("   Get your API key from: https://elevenlabs.io/")
        return False

    if api_key == "your-elevenlabs-api-key":
        print("❌ ERROR: ELEVENLABS_API_KEY is still set to placeholder value")
        print("   Replace with your actual API key from https://elevenlabs.io/")
        return False

    print("✓ Environment variables are set")
    print()

    # Step 2: Test API connection
    print("Step 2: Testing API connection...")

    try:
        from elevenlabs import voices, set_api_key

        # Set the API key
        set_api_key(api_key)

        print("✓ ElevenLabs API key configured")
        print()

    except Exception as e:
        print(f"❌ ERROR: Failed to import ElevenLabs: {str(e)}")
        return False

    # Step 3: Verify API key by listing voices
    print("Step 3: Verifying API key by listing available voices...")

    try:
        voice_list = voices()

        if not voice_list:
            print("⚠️  WARNING: API key works but no voices found")
            print("   This is unusual. Check your account status.")
            print()
        else:
            print(f"✓ API key verified! Found {len(voice_list)} voices")
            print()

    except Exception as e:
        error_msg = str(e)

        if "401" in error_msg or "unauthorized" in error_msg.lower():
            print("❌ ERROR: Invalid API key")
            print(f"   Error: {error_msg}")
            print()
            print("   Please check your API key at: https://elevenlabs.io/")
            return False
        elif "403" in error_msg or "forbidden" in error_msg.lower():
            print("❌ ERROR: API key valid but access forbidden")
            print(f"   Error: {error_msg}")
            print()
            print("   Your account may be suspended or have restrictions.")
            return False
        elif "permission" in error_msg.lower() and "voices_read" in error_msg.lower():
            print("⚠️  WARNING: API key is valid but has limited permissions")
            print(f"   Error: {error_msg}")
            print()
            print("   Your API key works but cannot list voices.")
            print("   This is OK - you can still generate speech!")
            print()
            # Set voice_list to empty to skip voice verification
            voice_list = []
        elif "429" in error_msg or "rate limit" in error_msg.lower():
            print("⚠️  WARNING: Rate limit exceeded")
            print(f"   Error: {error_msg}")
            print()
            print("   Your API key works but you've hit rate limits. Try again later.")
            voice_list = []
        else:
            print(f"❌ ERROR: API request failed: {error_msg}")
            return False

    # Step 4: Verify voice ID (if set)
    if voice_id and voice_id != "your-default-voice-id" and voice_list:
        print("Step 4: Verifying voice ID...")

        try:
            # Check if the voice ID exists in the list
            voice_found = None
            for v in voice_list:
                if v.voice_id == voice_id:
                    voice_found = v
                    break

            if voice_found:
                print(f"✓ Voice ID verified: {voice_found.name}")
                print(f"  Voice ID: {voice_found.voice_id}")
                if hasattr(voice_found, 'category'):
                    print(f"  Category: {voice_found.category}")
                print()
            else:
                print(f"⚠️  WARNING: Voice ID '{voice_id}' not found")
                print()
                print("   Available voices:")
                for v in voice_list[:5]:
                    print(f"     - {v.name}: {v.voice_id}")
                if len(voice_list) > 5:
                    print(f"     ... and {len(voice_list) - 5} more")
                print()

        except Exception as e:
            print(f"⚠️  WARNING: Could not verify voice ID: {str(e)}")
            print()
    elif not voice_list:
        print("Step 4: Skipping voice verification (cannot list voices)")
        print(f"  Using configured voice ID: {voice_id}")
        print()
    else:
        print("Step 4: Voice ID not set or using placeholder")
        print("  You can set a specific voice ID in .env")
        print("  Using default voice for now")
        print()

    # Step 5: Show available voices
    if voice_list:
        print("Step 5: Listing available voices...")

        try:
            print(f"\nFound {len(voice_list)} voices in your account:")
            print()

            # Group by category if available
            categories = {}
            for voice in voice_list:
                category = getattr(voice, 'category', 'uncategorized')
                if category not in categories:
                    categories[category] = []
                categories[category].append(voice)

            for category, voices_in_cat in sorted(categories.items()):
                print(f"  {category.upper()}:")
                for voice in voices_in_cat[:10]:  # Limit to 10 per category
                    print(f"    - {voice.name}: {voice.voice_id}")
                if len(voices_in_cat) > 10:
                    print(f"    ... and {len(voices_in_cat) - 10} more")
                print()

        except Exception as e:
            print(f"⚠️  Could not list voices: {str(e)}")
            print()
    else:
        print("Step 5: Skipping voice listing (limited API permissions)")
        print()

    # Success summary
    print("=" * 60)
    print("✓ ELEVENLABS CREDENTIALS TEST PASSED")
    print("=" * 60)
    print()
    print("Your ElevenLabs API credentials are properly configured!")
    print()
    print("Next steps:")
    print("  1. Choose a voice ID from the list above (optional)")
    print("  2. Update ELEVENLABS_VOICE_ID in .env with your preferred voice")
    print("  3. Start generating speech with the workflow!")
    print()
    print("Example usage:")
    print("  python cli.py generate \\")
    print("    --scene-id test \\")
    print("    --prompt \"A test scene\" \\")
    print("    --dialogue \"Hello, this is a test.\"")
    print()

    return True


if __name__ == "__main__":
    try:
        success = test_elevenlabs_credentials()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
