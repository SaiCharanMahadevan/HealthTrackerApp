import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import logging # Import logging
from app.core.config import settings
from typing import Optional, Dict, Any

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

def parse_health_entry_text(text: str) -> Dict[str, Any]:
    """Parses natural language text using Gemini, with enhanced prompt and validation."""
    logger.info(f"Attempting LLM parse for text: '{text[:100]}...'") # Log input text
    
    # --- Enhanced Prompt --- 
    prompt_parts = [
      f"Input Text: \"{text}\"",
      "Task: Analyze the input text, which is a health log entry. Identify the primary entry type ('food', 'weight', 'steps', or 'unknown'). Extract relevant structured data into a JSON object.",
      "Instructions:",
      "1. Determine the type ('food', 'weight', 'steps', 'unknown').",
      "2. If 'food': Identify each item. \"\n         - If the input specifies a **total weight or volume** for an item (e.g., '50g shrimp', '200ml milk'): \"\n           \"  Set 'quantity' to 1. \"\n           \"  Set 'unit' to 'serving' or omit it. \"\n           \"  Add 'specified_amount': <number> and 'specified_unit': '<weight/volume unit>' to the item object.\"\n           \"  Calculate nutritional values (calories, protein_g, carbs_g, fat_g) for **that specific total amount** and include them in the item object.\"\n         - If the input specifies a **count** of items (e.g., '2 apples', '1 slice bread', '12 cashews'): \"\n           \"  Set 'quantity' to the count. \"\n           \"  Set 'unit' to an appropriate descriptor (e.g., 'medium', 'slice', 'piece', 'nut') or omit it.\"\n           \"  Do NOT add 'specified_amount' or 'specified_unit'.\"\n           \"  Calculate nutritional values (calories, protein_g, carbs_g, fat_g) **per ONE SINGLE UNIT/PIECE**. Be realistic: the nutrition for one small piece (like a single nut or grape) will be much lower than a standard serving size (like 1 oz or 100g). Estimate for the single piece only.\"\n         - Ensure all fields ('items' list, 'total_calories', 'total_protein_g', 'total_carbs_g', 'total_fat_g') are present in the 'parsed_data' object. \"\n         \"- IMPORTANT: The 'total_...' fields should always represent the final sum for the entire entry, correctly calculated based on item nutrition and quantity (whether quantity is a count or represents a single serving of a specified amount).\",",
      "3. If 'weight': Extract value and unit (kg or lbs). Ensure 'value' and 'unit' fields are present.",
      "4. If 'steps': Extract the step count. Ensure 'value' field is present.",
      "5. If 'unknown' or cannot parse reliably: Set type to 'unknown'.",
      "Accuracy Emphasis: Prioritize accurate numerical estimations, especially for calories and macronutrients based on common knowledge, calculated for the specified quantities or amounts.",
      "Output Format: Respond ONLY with the JSON object adhering to the structure below. Do not include explanations or markdown formatting.",
      "JSON Structures:",
      "  Food: {\"type\": \"food\", \"parsed_data\": {\"items\": [{\"quantity\": <num>, \"unit\": \"<str>\", \"item\": \"<str>\", \"calories\": <num>, \"protein_g\": <num>, \"carbs_g\": <num>, \"fat_g\": <num>}], \"total_calories\": <num>, \"total_protein_g\": <num>, \"total_carbs_g\": <num>, \"total_fat_g\": <num>}} (Ensure all total fields are included)",
      "  Weight: {\"type\": \"weight\", \"value\": <num>, \"unit\": \"<str>\"} (Ensure value and unit)",
      "  Steps: {\"type\": \"steps\", \"value\": <num>} (Ensure value)",
      "  Unknown: {\"type\": \"unknown\"}",
      "Example for specified weight:",
      "  Input: 50g shrimp cooked",
      "  Output: {\"type\": \"food\", \"parsed_data\": {\"items\": [{\"quantity\": 50, \"unit\": \"g\", \"item\": \"shrimp cooked\", \"calories\": 49, \"protein_g\": 12, \"carbs_g\": 0, \"fat_g\": 0.2}], \"total_calories\": 49, \"total_protein_g\": 12, \"total_carbs_g\": 0, \"total_fat_g\": 0.2}} (Nutritional values calculated for the total 50g specified)",
      "  Item specified by count (large item): {\"quantity\": 2, \"unit\": \"medium\", \"item\": \"apple\", \"calories\": 95, \"protein_g\": 0.5, \"carbs_g\": 25, \"fat_g\": 0.3} (Nutrition is PER apple)",
      "  Item specified by count (small item): {\"quantity\": 12, \"unit\": \"piece\", \"item\": \"cashew nut\", \"calories\": 9, \"protein_g\": 0.3, \"carbs_g\": 0.5, \"fat_g\": 0.7} (Nutrition is PER SINGLE cashew piece)",
      "  Item specified by count (small item): {\"quantity\": 7, \"unit\": \"piece\", \"item\": \"walnut\", \"calories\": 26, \"protein_g\": 0.6, \"carbs_g\": 0.2, \"fat_g\": 2.6} (Nutrition is PER SINGLE walnut piece)",
      "  Item specified by weight: {\"quantity\": 1, \"unit\": \"serving\", \"item\": \"shrimp cooked\", \"specified_amount\": 50, \"specified_unit\": \"g\", \"calories\": 49, \"protein_g\": 12, \"carbs_g\": 0, \"fat_g\": 0.2} (Nutrition is FOR THE TOTAL 50g)",
      "(Include these items within the 'parsed_data'.'items' list. The 'total_...' fields in 'parsed_data' should sum these correctly)"
    ]

    try:
        response = model.generate_content(prompt_parts)
        
        if not response.parts:
             logger.warning(f"LLM response blocked or empty for text: '{text[:100]}...'")
             return {"type": "error", "error_detail": "LLM response blocked or empty"}

        raw_output = response.text.strip()
        if raw_output.startswith("```json"):
            raw_output = raw_output[7:]
        if raw_output.endswith("```"):
            raw_output = raw_output[:-3]
        raw_output = raw_output.strip()
        
        logger.info(f"LLM raw output received: {raw_output}") # Log raw output
        
        parsed_json = json.loads(raw_output)
        
        # --- Validate Structure --- 
        if not _validate_parsed_data(parsed_json):
            logger.warning(f"Parsed JSON failed validation for text: '{text[:100]}...'. Result: {parsed_json}")
            # Return as 'unknown' but include original parsed data for potential debugging/storage
            return {"type": "unknown", "error_detail": "Parsed JSON failed validation", "original_llm_output": parsed_json}
        
        logger.info(f"LLM parse successful and validated for text: '{text[:100]}...'") # Log success
        return parsed_json # Return validated JSON
        
    except json.JSONDecodeError as e:
        logger.error(f"LLM JSON parsing failed for text: '{text[:100]}...'. Raw output: {raw_output}. Error: {e}", exc_info=False) # exc_info=False for brevity
        return {"type": "error", "error_detail": "LLM output was not valid JSON"}
    except Exception as e:
        # Catch other potential API errors (network, config, etc.)
        logger.error(f"LLM generation failed for text: '{text[:100]}...'. Error: {e}", exc_info=True)
        return {"type": "error", "error_detail": f"LLM generation failed: {e}"} # Return error structure

# Example usage (for testing):
# if __name__ == "__main__":
#     test_text = "Had 2 eggs and a slice of toast for breakfast, weight 81kg"
#     result = parse_health_entry_text(test_text)
#     print(result) 