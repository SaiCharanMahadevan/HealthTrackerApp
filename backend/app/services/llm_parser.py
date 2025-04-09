import google.generativeai as genai
import os
from typing import Optional, Dict, Any
import json
import logging # Import logging
from app.core.config import settings
import io
from PIL import Image # Need Pillow installed (pip install Pillow)

logger = logging.getLogger(__name__) # Get logger

# Configure the Gemini API client
genai.configure(api_key=settings.GOOGLE_API_KEY)

# Define the generation config and safety settings (adjust as needed)
generation_config = {
"temperature": 0.3,
    "top_p": 1,
    "top_k": 1,
"max_output_tokens": 2048,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

def _validate_parsed_data(parsed_json: Dict[str, Any]) -> bool:
    """Basic validation for expected keys based on type."""
    entry_type = parsed_json.get('type')
    if not entry_type:
        return False
    
    if entry_type == 'food':
        parsed_data = parsed_json.get('parsed_data')
        # Check existence of keys, not necessarily non-null values here
        if not isinstance(parsed_data, dict) or \
           'items' not in parsed_data or \
           'total_calories' not in parsed_data or \
           'total_protein_g' not in parsed_data or \
           'total_carbs_g' not in parsed_data or \
           'total_fat_g' not in parsed_data:
            logger.warning(f"Food entry parsed JSON missing expected keys: {parsed_json}")
            return False
        # Could add more checks on item structure if needed
        
    elif entry_type == 'weight':
        if 'value' not in parsed_json or 'unit' not in parsed_json:
            logger.warning(f"Weight entry parsed JSON missing value or unit: {parsed_json}")
            return False
        
    elif entry_type == 'steps':
        if 'value' not in parsed_json:
            logger.warning(f"Steps entry parsed JSON missing value: {parsed_json}")
            return False
        
    elif entry_type == 'unknown' or entry_type == 'error':
        pass # Allow these types through
        
    else:
        logger.warning(f"Unrecognized entry type in parsed JSON: {entry_type}")
        return False # Treat unrecognized types as invalid for structure check
        
    return True

def _parse_llm_response_to_dict(response_text: str) -> Dict[str, Any]:
    """Helper to attempt parsing LLM JSON response."""
    try:
        # Attempt to find JSON block
        json_start = response_text.find('```json')
        json_end = response_text.rfind('```')
        if json_start != -1 and json_end != -1:
            json_str = response_text[json_start + 7:json_end].strip()
            parsed = json.loads(json_str)
            if isinstance(parsed, dict):
                return parsed
        
        # Fallback if no JSON block or parsing failed
        logger.warning(f"Could not parse LLM response as JSON, returning raw text: {response_text[:100]}...")
        return {"type": "unknown", "raw_response": response_text}
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error parsing LLM response: {e}", exc_info=True)
        return {"type": "error", "error_detail": "Failed to decode LLM JSON response", "raw_response": response_text}
    except Exception as e:
        logger.error(f"Unexpected error parsing LLM response: {e}", exc_info=True)
        return {"type": "error", "error_detail": "Unexpected error parsing LLM response", "raw_response": response_text}

def parse_health_entry_text(text: Optional[str], image_data: Optional[bytes] = None) -> Dict[str, Any]:
    """Parses health entry text and/or image using the appropriate Gemini model."""
    
    logger.info(f"Parsing health entry. Text provided: {bool(text)}. Image data provided: {bool(image_data)}")

    if not text and not image_data:
        logger.warning("parse_health_entry_text called with no text and no image data.")
        return {"type": "error", "error_detail": "No text or image provided for parsing"}

    # Define the base prompt structure (adjust as needed)
    prompt_instruction = """
    Analyze the following health log entry (text and/or image).
    Identify the type of entry (e.g., 'food', 'weight', 'steps', 'exercise', 'medication', 'symptom', 'note').
    Extract key information relevant to the type.
    For 'food', list items with quantity, unit, and provide your BEST ESTIMATE for nutritional values (calories, protein_g, carbs_g, fat_g). If nutritional values are completely unknown or cannot be reasonably estimated, use null. Calculate totals based on your estimates.
    For 'weight', extract value and unit (prefer kg).
    For 'steps', extract value.
    For others, provide a brief summary.
    Return the result ONLY as a JSON object within ```json ... ``` tags.
    Example Food Output:
    ```json
    {
      "type": "food",
      "parsed_data": {
        "items": [
          {"item": "Apple", "quantity": 1, "unit": "piece", "calories": 95, "protein_g": 0.5, "carbs_g": 25, "fat_g": 0.3},
          {"item": "Banana", "quantity": 1, "unit": "piece", "calories": 105, "protein_g": 1.3, "carbs_g": 27, "fat_g": 0.4}
        ],
        "total_calories": 200,
        "total_protein_g": 1.8,
        "total_carbs_g": 52,
        "total_fat_g": 0.7
      }
    }
    ```
    Example Weight Output:
    ```json
    {
      "type": "weight",
      "value": 75.5,
      "unit": "kg",
      "parsed_data": { "original_text": "Weight 75.5 kg" }
    }
    ```
    If the input cannot be reliably parsed, return:
    ```json
    { "type": "unknown", "parsed_data": { "original_text": "..." } }
    ```
    """

    try:
        if image_data:
            logger.debug("Image data provided, attempting multi-modal parsing.")
            try:
                # Attempt to open image to validate and get format
                img = Image.open(io.BytesIO(image_data))
                # Gemini supports PNG, JPEG, WEBP, HEIC, HEIF
                mime_type = Image.MIME.get(img.format)
                if not mime_type or not mime_type.startswith('image/'):
                    raise ValueError(f"Unsupported image format: {img.format}")
                logger.debug(f"Detected image format: {img.format} ({mime_type})")

                # --- Use gemini-1.5-pro-latest for multi-modal --- 
                vision_model = genai.GenerativeModel(
                    'gemini-2.0-flash-exp', 
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
                prompt_parts = [prompt_instruction]
                if text:
                    prompt_parts.append(text)
                prompt_parts.append({"mime_type": mime_type, "data": image_data})
                
                response = vision_model.generate_content(prompt_parts)
                # --- End model usage change ---
                
                logger.info("Multi-modal LLM call successful.")
                return _parse_llm_response_to_dict(response.text)

            except Exception as img_e:
                logger.error(f"Multi-modal LLM attempt failed (image error or API call): {img_e}", exc_info=True)
                # Fallback to text-only if image processing fails and text exists?
                if text:
                    logger.warning("Falling back to text-only parsing due to image processing/API error.")
                    # Continue to text-only block below
                else:
                    # If only image was provided and it failed, return error
                    return {"type": "error", "error_detail": f"Image processing failed: {img_e}"} 
        
        # --- Text-Only Processing --- 
        # This block executes if image_data is None OR if image processing failed and we fell back
        if text:
            logger.debug("Using text-only parsing.")
            # --- Use gemini-1.5-flash for text-only --- 
            text_model = genai.GenerativeModel(
                'gemini-2.0-flash-exp',
                generation_config=generation_config,
                safety_settings=safety_settings
            ) 
            prompt_parts = [prompt_instruction, text]
            response = text_model.generate_content(prompt_parts)
            # --- End model usage change ---
            
            logger.info("Text-only LLM call successful.")
            return _parse_llm_response_to_dict(response.text)
        else:
            # This case should theoretically not be reached if the initial check passed,
            # but included for robustness.
            logger.error("parse_health_entry_text reached text-only block without text.")
            return {"type": "error", "error_detail": "Parsing attempted without text after image failure."}

    except Exception as e:
        # Catch potential errors during model instantiation or general API issues
        logger.error(f"LLM parsing failed: {e}", exc_info=True)
        return {"type": "error", "error_detail": str(e), "raw_response": None}

# Example usage (for testing):
# if __name__ == "__main__":
#     test_text = "Had 2 eggs and a slice of toast for breakfast, weight 81kg"
#     result = parse_health_entry_text(test_text)
#     print(result) 