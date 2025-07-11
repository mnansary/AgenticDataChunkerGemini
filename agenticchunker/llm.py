from agenticchunker.constants import API_KEY_CSV_PATH, MODEL_NAME
from agenticchunker.client_handler import create_client_manager # Assuming this creates the ApiKeyManager
from loguru import logger
from typing import Optional # Import Optional for type hinting

# This assumes 'cm' is a global instance of ApiKeyManager
# It's good practice to initialize it once at the start of your application.
logger.info("Initializing the global API Key Manager...")
cm = create_client_manager(API_KEY_CSV_PATH)
logger.info("API Key Manager initialized.")


def call_llm(prompt, gen_config) -> Optional[str]:
    """
    Makes a call to the generative language model using a managed client.

    This function handles acquiring a client from the pool, making the API call,
    and managing exceptions. The client acquisition will block and wait according
    to the defined global and per-key cooldown rules.

    Args:
        prompt: The input prompt for the model.
        gen_config: The generation configuration for the model.

    Returns:
        The model's response text as a string, or None if an error occurred.
    """
    try:
        # 1. Get a client. This will block until one is available.
        logger.info("Acquiring a client from the manager...")
        client = cm.get_client()
        logger.success(f"Client acquired. Making API call with model '{MODEL_NAME}'.")

        # 2. Make the API call with the corrected method and parameters.
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=gen_config, # Correct parameter name
        )
        
        # Note: The Google SDK can sometimes return a response with no 'text' part
        # if the content was blocked. It's good practice to check for this.
        
        return response.text
        
    except Exception as e:
        # 3. Log errors appropriately and return None for failure.
        logger.error(f"An exception occurred during the LLM call: {e}")
        # Re-raising or handling specific exceptions (like auth errors, quota errors)
        # can also be a valid strategy depending on your needs.
        return None