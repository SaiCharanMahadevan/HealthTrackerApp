import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Open Food Facts API endpoint
OFF_API_URL = "https://world.openfoodfacts.org/api/v2/search"

def get_nutrition_from_off(item_name: str) -> Optional[Dict[str, Any]]:
    """
    Searches Open Food Facts for an item and returns nutritional data per 100g.
    Returns None if not found or data is insufficient.
    """
    logger.info(f"Querying Open Food Facts for: {item_name}")
    params = {
        "search_terms": item_name,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 1, # Get only the top result for simplicity
        # Request specific fields for efficiency
        "fields": "product_name,nutriments" 
    }
    
    try:
        response = requests.get(OFF_API_URL, params=params, timeout=10) # Added timeout
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        
        data = response.json()
        
        if not data or data.get('count', 0) == 0 or not data.get('products'):
            logger.info(f"No products found on OFF for: {item_name}")
            return None
            
        product = data['products'][0]
        nutriments = product.get('nutriments')
        
        if not nutriments:
            logger.info(f"No nutriments data found on OFF for product: {product.get('product_name')}")
            return None
            
        # Extract relevant values per 100g. Keys might vary (e.g., energy-kcal_100g or energy_100g)
        # Check common variations for calories
        calories_100g = nutriments.get('energy-kcal_100g') or \
                        nutriments.get('energy_100g') # Often in kJ, needs conversion if only this available
        # TODO: Add kJ to kcal conversion if needed: kj / 4.184 approx
                        
        protein_100g = nutriments.get('proteins_100g')
        carbs_100g = nutriments.get('carbohydrates_100g')
        fat_100g = nutriments.get('fat_100g')
        
        # Check if essential data is present
        if calories_100g is None or protein_100g is None or carbs_100g is None or fat_100g is None:
            logger.warning(f"Incomplete nutriments data from OFF for: {product.get('product_name')}")
            return None
            
        # Return data per 100g
        nutrition_data = {
            "calories_100g": float(calories_100g),
            "protein_100g": float(protein_100g),
            "carbs_100g": float(carbs_100g),
            "fat_100g": float(fat_100g),
            "source": "OpenFoodFacts",
            "product_name": product.get('product_name') # Include name for logging/debug
        }
        logger.info(f"Found OFF data for '{item_name}' ('{nutrition_data['product_name']}')") #: {nutrition_data}") # Simplified log
        return nutrition_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error querying Open Food Facts API: {e}", exc_info=False)
        return None
    except (KeyError, IndexError, ValueError, json.JSONDecodeError) as e:
        logger.error(f"Error processing Open Food Facts response: {e}", exc_info=False)
        return None 