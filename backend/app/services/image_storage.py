# backend/app/services/image_storage.py
import os
import uuid
from fastapi import UploadFile
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Define storage path (make configurable later)
UPLOAD_DIR = "static/uploads" 
# Ensure this directory exists relative to where you run uvicorn
os.makedirs(UPLOAD_DIR, exist_ok=True) 

def save_upload_file(upload_file: UploadFile) -> Optional[str]:
    """Saves uploaded file to local dir and returns its URL path."""
    try:
        # Create unique filename
        # Ensure filename is secure, avoid path traversal (though uuid helps)
        ext = os.path.splitext(upload_file.filename)[1]
        # Basic validation for common image extensions
        if ext.lower() not in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
             logger.warning(f"Attempted to upload non-image file extension: {ext}")
             return None # Or raise an error
        
        filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        # Read the file content safely
        # Consider adding size limit checks here before reading
        # content = await upload_file.read() # Use await if function is async
        content = upload_file.file.read()
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Return URL path relative to static mount
        url_path = f"/static/uploads/{filename}" 
        logger.info(f"Image saved locally to {file_path}, URL path: {url_path}")
        return url_path
    except Exception as e:
        logger.error(f"Failed to save upload file {upload_file.filename}: {e}", exc_info=True)
        return None 