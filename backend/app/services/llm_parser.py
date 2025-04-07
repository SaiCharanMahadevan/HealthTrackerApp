import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import logging # Import logging
from app.core.config import settings
from typing import Optional, Dict, Any
import io
from PIL import Image # Need Pillow installed (pip install Pillow)

logger = logging.getLogger(__name__) # Get logger

load_dotenv()

# Configure the Gemini API client
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

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

# Choose the model
model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",
                              generation_config=generation_config,
                              safety_settings=safety_settings)

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

def parse_health_entry_text(
    text: Optional[str] = None, 
    image_data: Optional[bytes] = None
) -> Dict[str, Any]:
    """Parses health entry text and/or image using Gemini multimodal capabilities."""
    
    if not text and not image_data:
        logger.error("LLM Parser: Both text and image data are missing.")
        return {"type": "error", "error_detail": "No input text or image provided."}

    log_text = text[:100] if text else "[No Text]"
    log_image = "[Image Provided]" if image_data else "[No Image]"
    logger.info(f"Attempting LLM parse for: Text='{log_text}...', Image={log_image}")

    # --- Construct Prompt --- 
    prompt_parts = []

    # Add image data first if present
    if image_data:
        try:
            img = Image.open(io.BytesIO(image_data))
            prompt_parts.append(img) # Add PIL image object to prompt
            logger.debug("Added image data to prompt parts.")
        except Exception as img_err:
            logger.error(f"Failed to process image data: {img_err}", exc_info=True)
            return {"type": "error", "error_detail": "Invalid image data provided."}

    # Add text instructions
    if text:
        prompt_parts.append(f"Input Text: \"{text}\" (Consider this text alongside the image if provided). ")
    else:
        prompt_parts.append("Input Text: [NONE] - Analyze the image only.")

    prompt_parts.extend([
      "Task: Analyze the input text and/or image, which is a health log entry. Identify the primary entry type ('food', 'weight', 'steps', or 'unknown'). Extract relevant structured data into a JSON object.",
      "Instructions:",
      "1. Prioritize image analysis if provided for 'food' type. If the text clearly indicates 'steps' or 'weight', ignore the image for nutritional analysis.",
      "2. Determine the type ('food', 'weight', 'steps', 'unknown').",
      "3. If 'food': Identify food items visible in the image or mentioned in text. Estimate quantity, units, and nutritional values (calories, protein_g, carbs_g, fat_g) for each identified item. Calculate totals.",
      "4. If 'weight' (based on text only): Extract value and unit.",
      "5. If 'steps' (based on text only): Extract the step count.",
      "6. If 'unknown' or cannot parse reliably: Set type to 'unknown'.",
      "Accuracy Emphasis: Prioritize accurate numerical estimations, especially for calories and macronutrients based on common knowledge.",
      "Output Format: Respond ONLY with the JSON object. Do not include explanations or markdown.",
      "JSON Structures:",
      "  Food: {\"type\": \"food\", \"parsed_data\": {\"items\": [{\"quantity\": <num>, \"unit\": \"<str>\", \"item\": \"<str>\", \"calories\": <num>, \"protein_g\": <num>, \"carbs_g\": <num>, \"fat_g\": <num>}], \"total_calories\": <num>, \"total_protein_g\": <num>, \"total_carbs_g\": <num>, \"total_fat_g\": <num>}} (Ensure all total fields are included)",
      "  Weight: {\"type\": \"weight\", \"value\": <num>, \"unit\": \"<str>\"} (Ensure value and unit)",
      "  Steps: {\"type\": \"steps\", \"value\": <num>} (Ensure value)",
      "  Unknown: {\"type\": \"unknown\"}",
    ])

    try:
        # Generate content using the potentially multimodal prompt
        response = model.generate_content(prompt_parts)
        
        # ... (Rest of response handling, JSON parsing, validation logic remains mostly the same) ...
        if not response.parts:
             logger.warning(f"LLM response blocked or empty for text: '{log_text}...'")
             return {"type": "error", "error_detail": "LLM response blocked or empty"}

        raw_output = response.text.strip()
        # ... (JSON cleaning logic) ...
        if raw_output.startswith("```json"):
            raw_output = raw_output[7:]
        if raw_output.endswith("```"):
            raw_output = raw_output[:-3]
        raw_output = raw_output.strip()
        
        logger.info(f"LLM raw output received: {raw_output}")
        
        parsed_json = json.loads(raw_output)
        
        if not _validate_parsed_data(parsed_json):
            logger.warning(f"Parsed JSON failed validation for text: '{log_text}...'. Result: {parsed_json}")
            return {"type": "unknown", "error_detail": "Parsed JSON failed validation", "original_llm_output": parsed_json}
        
        logger.info(f"LLM parse successful and validated for text: '{log_text}...'")
        return parsed_json
        
    except json.JSONDecodeError as e:
        logger.error(f"LLM JSON parsing failed for text: '{log_text}...'. Raw output: {raw_output}. Error: {e}", exc_info=False)
        return {"type": "error", "error_detail": "LLM output was not valid JSON"}
    except Exception as e:
        logger.error(f"LLM generation failed for text: '{log_text}...'. Error: {e}", exc_info=True)
        return {"type": "error", "error_detail": f"LLM generation failed: {e}"}

# Example usage (for testing):
# if __name__ == "__main__":
#     test_text = "Had 2 eggs and a slice of toast for breakfast, weight 81kg"
#     result = parse_health_entry_text(test_text)
#     print(result) 