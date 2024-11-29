import importlib.resources
import json

def load_json(file_name):
    try:
        # Use importlib to access the file in the installed package
        with importlib.resources.open_text("Assessment", file_name) as f:
            return json.load(f)
    except FileNotFoundError:
        raise Exception(f"{file_name} not found in Assessment package.")
    except json.JSONDecodeError as e:
        raise Exception(f"Error decoding JSON: {e}")
