"""
ImageKit upload tool — store documents in ImageKit.

Converted from the user's FastAPI route into a standalone function.
"""

import os
import base64
from imagekitio import ImageKit
from google.adk.tools import FunctionTool
from config.settings import IMAGEKIT_PRIVATE_KEY, IMAGEKIT_PUBLIC_KEY, IMAGEKIT_URL_ENDPOINT


def _get_imagekit_client() -> ImageKit:
    """Return a configured ImageKit client."""
    return ImageKit(
        private_key=IMAGEKIT_PRIVATE_KEY,
        public_key=IMAGEKIT_PUBLIC_KEY,
        url_endpoint=IMAGEKIT_URL_ENDPOINT,
    )


class _UploadOptions:
    """ImageKit upload options."""
    def __init__(self, folder, use_unique_file_name, is_private_file):
        self.folder = folder
        self.use_unique_file_name = use_unique_file_name
        self.is_private_file = is_private_file


def upload_to_imagekit(filepath: str, file_name: str) -> dict:
    """Upload a local file to ImageKit for cloud storage.

    Args:
        filepath: Path to the local file to upload.
        file_name: Name to give the uploaded file (e.g. 'pan_johndoe.pdf').

    Returns:
        Dictionary with the public URL and file ID from ImageKit.
    """
    if not os.path.exists(filepath):
        return {"url": "", "file_id": "", "file_name": file_name, "error": "File not found"}

    with open(filepath, "rb") as f:
        file_bytes = f.read()
    standard_base64 = base64.b64encode(file_bytes).decode()

    ik = _get_imagekit_client()

    options = _UploadOptions(
        folder="/hr_documents/",
        use_unique_file_name=True,
        is_private_file=False,
    )

    upload_response = ik.upload_file(
        file=standard_base64,
        file_name=file_name,
        options=options,
    )

    return {
        "url": upload_response.url,
        "file_id": upload_response.file_id,
        "file_name": file_name,
    }


# ── ADK FunctionTool wrapper ──────────────────────────────
upload_to_imagekit_tool = FunctionTool(func=upload_to_imagekit)
