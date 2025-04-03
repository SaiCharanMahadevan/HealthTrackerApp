import google.generativeai as genai
import json
from app.core.config import settings
from typing import Optional, Dict, Any

# Configure the Gemini client
try:
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    # Set up the model
    generation_config = {
        "temperature": 0.2, # Lower temperature for more deterministic output
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": 2048, # Adjust as needed
    }
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash", # Or another suitable model
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    print("Gemini model configured successfully.")
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    model = None

def parse_health_entry_text(text: str) -> Optional[Dict[str, Any]]:
    """Sends the health entry text to Gemini for parsing and returns structured data."""
    if not model:
        print("Gemini model not initialized.")
        return None

    # --- Prompt Engineering --- 
    # This is the critical part and needs careful design.
    # We need to instruct the model to:
    # 1. Identify the type of entry (food, weight, steps).
    # 2. Extract relevant values (e.g., food items, weight value, step count).
    # 3. For food, estimate calories and macronutrients (protein, carbs, fat).
    # 4. Return the result in a structured JSON format.
    
    prompt = f"""
    Analyze the following health entry text and extract structured information.
    The possible entry types are 'food', 'weight', or 'steps'.
    
    Input Text: "{text}"
    
    Output the result as a JSON object with the following structure:
    - If type is 'food': {{ "type": "food", "items": [ {{ "item": "<food item description>", "quantity": <numeric quantity>, "unit": "<unit e.g., piece, gram, cup>", "calories": <estimated calories>, "protein_g": <estimated protein grams>, "carbs_g": <estimated carbohydrate grams>, "fat_g": <estimated fat grams> }} ], "total_calories": <total calories for all items>, "total_protein_g": <...>, "total_carbs_g": <...>, "total_fat_g": <...> }}
    - If type is 'weight': {{ "type": "weight", "value": <numeric weight>, "unit": "<unit e.g., kg, lbs>" }}
    - If type is 'steps': {{ "type": "steps", "value": <numeric step count> }}
    - If the text doesn't match any type or is unclear, return: {{ "type": "unknown" }}

    Example Input: "Had 2 slices of whole wheat toast with avocado and one fried egg for breakfast, weight 75.2kg"
    Example Output: {{ "type": "food", "items": [ {{ "item": "whole wheat toast", "quantity": 2, "unit": "slices", "calories": 160, "protein_g": 6, "carbs_g": 30, "fat_g": 2 }}, {{ "item": "avocado", "quantity": 0.5, "unit": "medium", "calories": 160, "protein_g": 2, "carbs_g": 9, "fat_g": 15 }}, {{ "item": "fried egg", "quantity": 1, "unit": "large", "calories": 90, "protein_g": 6, "carbs_g": 1, "fat_g": 7 }} ], "total_calories": 410, "total_protein_g": 14, "total_carbs_g": 40, "total_fat_g": 24 }}
    (Note: If multiple types are in one text, prioritize food, or handle separately based on requirements. The above example simplified to food). Provide only the JSON object.
    """

    try:
        print(f"Sending prompt to Gemini for text: '{text}'")
        response = model.generate_content(prompt)
        
        # Debug: Print raw response text
        # print("Gemini raw response:", response.text)

        # Clean the response text to extract only the JSON part
        # Sometimes the model might add backticks or explanations
        json_text = response.text.strip().strip("`json\n").strip("`")
        
        parsed_data = json.loads(json_text)
        print(f"Successfully parsed Gemini response: {parsed_data}")
        return parsed_data
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from Gemini response: {e}")
        print(f"Problematic response text: {response.text}")
        return {"type": "error", "detail": "Failed to parse LLM response"}
    except Exception as e:
        print(f"Error during Gemini API call: {e}")
        return {"type": "error", "detail": str(e)}

# Example usage (for testing):
# if __name__ == "__main__":
#     test_text = "1 piece parotta from fair price and today's weight is 81 kgs"
#     parsed = parse_health_entry_text(test_text)
#     print("\nFinal Parsed Result:")
#     print(json.dumps(parsed, indent=2)) 