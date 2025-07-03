import json

def save_dict_to_json(data: dict, file_path: str, indent: int = 4):
    """
    Saves a dictionary to a JSON file.

    Args:
        data (dict): The dictionary to save.
        file_path (str): The output JSON file path.
        indent (int): Number of spaces for indentation (default: 4).
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
    except Exception as e:
        raise RuntimeError(f"Error saving JSON: {e}")
    

def read_markdown(file_path: str) -> str:
    """
    Reads a markdown file and returns its contents as a string.
    
    Args:
        file_path (str): The path to the markdown file.
    
    Returns:
        str: The contents of the markdown file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to read markdown file: {e}")

def read_json(file_path: str) -> dict:
    """
    Reads a JSON file and returns its content as a dictionary.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        dict: Parsed JSON data.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to read JSON file: {e}")