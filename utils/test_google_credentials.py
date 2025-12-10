#!/usr/bin/env python3
"""
Test Google Cloud credentials in isolation
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Get the project root directory (parent of utils/)
PROJECT_ROOT = Path(__file__).parent.parent

# Load environment variables from project root
load_dotenv(PROJECT_ROOT / ".env")


def test_credentials():
    """Test Google Cloud credentials"""

    print("=" * 60)
    print("Google Cloud Credentials Test")
    print("=" * 60)
    print()

    # Step 1: Check environment variables
    print("Step 1: Checking environment variables...")

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    location = os.getenv("VEO_LOCATION", "us-central1")

    print(f"  GOOGLE_CLOUD_PROJECT: {project_id or '[NOT SET]'}")
    print(f"  GOOGLE_APPLICATION_CREDENTIALS: {credentials_path or '[NOT SET]'}")
    print(f"  VEO_LOCATION: {location}")
    print()

    if not project_id:
        print("❌ ERROR: GOOGLE_CLOUD_PROJECT is not set in .env")
        print("   Add: GOOGLE_CLOUD_PROJECT=your-project-id")
        return False

    if not credentials_path:
        print("❌ ERROR: GOOGLE_APPLICATION_CREDENTIALS is not set in .env")
        print("   Add: GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json")
        return False

    print("✓ Environment variables are set")
    print()

    # Step 2: Check if credentials file exists
    print("Step 2: Checking if credentials file exists...")

    # Resolve path relative to project root if it's not absolute
    creds_path = Path(credentials_path)
    if not creds_path.is_absolute():
        creds_path = PROJECT_ROOT / credentials_path

    if not creds_path.exists():
        print(f"❌ ERROR: Credentials file not found")
        print(f"   Looking for: {credentials_path}")
        print(f"   Resolved to: {creds_path}")
        print(f"   Project root: {PROJECT_ROOT}")
        return False

    print(f"✓ Credentials file exists at: {creds_path}")
    # Update credentials_path to the resolved absolute path for later use
    credentials_path = str(creds_path)
    print()

    # Step 3: Try to load credentials
    print("Step 3: Loading credentials...")

    try:
        from google.oauth2 import service_account

        credentials = service_account.Credentials.from_service_account_file(
            credentials_path
        )

        print("✓ Successfully loaded credentials")
        print(f"  Service account email: {credentials.service_account_email}")
        print(f"  Project ID from credentials: {credentials.project_id}")
        print()

        # Check if project IDs match
        if credentials.project_id != project_id:
            print(f"⚠️  WARNING: Project ID mismatch!")
            print(f"   .env GOOGLE_CLOUD_PROJECT: {project_id}")
            print(f"   Credentials project_id: {credentials.project_id}")
            print()

    except Exception as e:
        print(f"❌ ERROR: Failed to load credentials: {str(e)}")
        return False

    # Step 4: Test authentication with Google Cloud
    print("Step 4: Testing authentication with Google Cloud...")

    try:
        from google.cloud import aiplatform

        aiplatform.init(
            project=project_id,
            location=location,
            credentials=credentials
        )

        print("✓ Successfully authenticated with Google Cloud")
        print(f"  Project: {project_id}")
        print(f"  Location: {location}")
        print()

    except Exception as e:
        print(f"❌ ERROR: Failed to authenticate: {str(e)}")
        print()
        print("Common issues:")
        print("  - Service account doesn't have necessary permissions")
        print("  - Vertex AI API is not enabled")
        print("  - Invalid credentials file")
        return False

    # Step 5: Check API access (optional, requires API to be enabled)
    print("Step 5: Checking Vertex AI API access...")

    try:
        # Try to list models (this will fail if API is not enabled)
        # This is a minimal test that doesn't require special permissions
        from google.cloud import aiplatform_v1

        client = aiplatform_v1.ModelServiceClient(credentials=credentials)
        parent = f"projects/{project_id}/locations/{location}"

        # Just test if we can make a request (even if it returns empty)
        request = aiplatform_v1.ListModelsRequest(
            parent=parent,
            page_size=1
        )

        # This will succeed if API is enabled, even with no models
        response = client.list_models(request=request)

        print("✓ Vertex AI API is accessible")
        print()

    except Exception as e:
        error_msg = str(e)

        if "403" in error_msg or "permission" in error_msg.lower():
            print("⚠️  WARNING: API is accessible but permissions may be limited")
            print(f"   Error: {error_msg}")
            print()
            print("   Your credentials work, but the service account may need additional roles:")
            print("   - Vertex AI User")
            print("   - Storage Object Viewer (if using Cloud Storage)")
            print()
        elif "not enabled" in error_msg.lower() or "404" in error_msg:
            print("⚠️  WARNING: Vertex AI API may not be enabled")
            print(f"   Error: {error_msg}")
            print()
            print("   Enable the API at:")
            print(f"   https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project={project_id}")
            print()
        else:
            print(f"⚠️  WARNING: Could not verify API access: {error_msg}")
            print()

    # Success summary
    print("=" * 60)
    print("✓ CREDENTIALS TEST PASSED")
    print("=" * 60)
    print()
    print("Your Google Cloud credentials are properly configured!")
    print()
    print("Next steps:")
    print("  1. Ensure Vertex AI API is enabled in your project")
    print("  2. Request access to Veo API (currently in preview)")
    print("  3. Grant your service account the 'Vertex AI User' role")
    print()

    return True


if __name__ == "__main__":
    try:
        success = test_credentials()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
