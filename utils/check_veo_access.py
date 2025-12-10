#!/usr/bin/env python3
"""
Check Veo API access and available models
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Get the project root directory (parent of utils/)
PROJECT_ROOT = Path(__file__).parent.parent

# Load environment variables from project root
load_dotenv(PROJECT_ROOT / ".env")


def check_veo_access():
    """Check if Veo API is accessible"""

    print("=" * 60)
    print("Veo API Access Check")
    print("=" * 60)
    print()

    # Step 1: Check environment variables
    print("Step 1: Checking environment variables...")

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("VEO_LOCATION", "us-central1")
    model_name = os.getenv("VEO_MODEL", "veo-001")
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    print(f"  GOOGLE_CLOUD_PROJECT: {project_id}")
    print(f"  VEO_LOCATION: {location}")
    print(f"  VEO_MODEL: {model_name}")
    print(f"  GOOGLE_APPLICATION_CREDENTIALS: {credentials_path}")
    print()

    if not project_id:
        print("❌ ERROR: GOOGLE_CLOUD_PROJECT is not set")
        return False

    # Step 2: Initialize Vertex AI
    print("Step 2: Initializing Vertex AI...")

    try:
        import vertexai
        from google.oauth2 import service_account

        # Resolve credentials path
        creds_path = Path(credentials_path)
        if not creds_path.is_absolute():
            creds_path = PROJECT_ROOT / credentials_path

        if creds_path.exists():
            credentials = service_account.Credentials.from_service_account_file(
                str(creds_path)
            )
            vertexai.init(
                project=project_id,
                location=location,
                credentials=credentials
            )
        else:
            vertexai.init(project=project_id, location=location)

        print(f"✓ Vertex AI initialized for {project_id} in {location}")
        print()

    except Exception as e:
        print(f"❌ ERROR: Failed to initialize Vertex AI: {str(e)}")
        return False

    # Step 3: Try to access Veo model
    print(f"Step 3: Checking access to Veo model ({model_name})...")

    try:
        from vertexai.generative_models import GenerativeModel

        model = GenerativeModel(model_name)
        print(f"✓ Successfully initialized model: {model_name}")
        print()

        # Try a simple test prompt
        print("Step 4: Testing video generation API...")
        test_prompt = "A serene lake at sunset"

        try:
            response = model.generate_content(test_prompt)
            print("✓ Model responded successfully!")
            print(f"  Response type: {type(response)}")
            print(f"  Response: {response}")
            print()
            return True

        except Exception as e:
            error_msg = str(e)

            if "404" in error_msg and "not found" in error_msg.lower():
                print("❌ ERROR: Veo model not found in your project")
                print(f"   Error: {error_msg}")
                print()
                print("   Possible reasons:")
                print("   1. Veo API access has not been granted to your project")
                print("   2. You're using the wrong model name")
                print("   3. Veo is not available in your selected region")
                print()
                print("   To get access to Veo:")
                print("   1. Visit: https://cloud.google.com/vertex-ai/generative-ai/docs/image/overview")
                print("   2. Request early access to Veo 2")
                print("   3. Enable Vertex AI Vision API in your project")
                print()
                return False

            elif "403" in error_msg or "permission" in error_msg.lower():
                print("❌ ERROR: Permission denied")
                print(f"   Error: {error_msg}")
                print()
                print("   Your service account may need additional permissions:")
                print("   - Vertex AI User")
                print("   - Vertex AI Service Agent")
                print()
                return False

            else:
                print(f"⚠️  WARNING: Unexpected error: {error_msg}")
                print()
                return False

    except ImportError as e:
        print(f"❌ ERROR: Failed to import required modules: {str(e)}")
        print()
        print("   Make sure you have installed:")
        print("   pip install google-cloud-aiplatform")
        return False

    except Exception as e:
        print(f"❌ ERROR: Failed to initialize model: {str(e)}")
        return False


if __name__ == "__main__":
    try:
        success = check_veo_access()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nCheck interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
