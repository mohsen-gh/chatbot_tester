
import json
from collections.abc import Iterator

import ijson
import utils.log_manager as log_manager
from schemas import TestCase, TurnResult

logger = log_manager.get_logger(__name__)


def stream_json_file(filepath: str, prefix: str = "test_cases.item") -> Iterator[TestCase]:
    """
    Stream JSON objects from a file and yield them as TestCase instances.
    This function reads a JSON file and iterates over items matching the specified
    prefix path, converting each item into a TestCase object.
    """
    try:
        with open(filepath, "rb") as f:
            for obj in ijson.items(f, prefix):
                try:
                    test_conv = TestCase(**obj)
                    yield test_conv
                except Exception as e:
                    # Catch Pydantic validation or parsing errors for individual items
                    logger.error(f"Error parsing item: {obj}. Error: {e}")
                    continue
    except ijson.JSONError as e:
        # Catch errors related to invalid JSON structure
        logger.error(f"Invalid JSON in file '{filepath}': {e}")
        return
    except FileNotFoundError:
        # Catch the error if the file doesn't exist at all
        logger.error(f"Json file not found: '{filepath}'. Please check the path.")
        return
    except IOError as e:
        # Catch other I/O issues (e.g., permission denied)
        logger.error(f"Could not read file '{filepath}': {e}")
        return
    except Exception as e:
        # Catch-all for unexpected issues
        logger.error(f"Unexpected error reading JSON from '{filepath}': {e}")


def append_to_jsonl(filepath: str, data: TurnResult) -> bool:
    """
    Appends a single dictionary as a JSON string to a file, forming a JSON Lines (JSONL) file.
    Returns True if successful, False otherwise.
    """
    try:
        # Open in append mode ('a') so we don't overwrite previous lines
        with open(filepath, "a", encoding="utf-8") as f:
            json.dump(data.model_dump(), f)
            f.write("\n")
        return True
        
    except TypeError as e:
        # Fails if 'data' contains objects json.dump cannot serialize (e.g., datetime, custom classes)
        logger.error(f"Failed to serialize data for JSONL file '{filepath}': {e}")
        return False
    except FileNotFoundError as e:
        # Fails if the directory path to the file does not exist
        logger.error(f"Directory does not exist for JSONL file '{filepath}': {e}")
        return False
    except IOError as e:
        # Fails due to permissions, disk space, or a locked file
        logger.error(f"IOError while appending to JSONL file '{filepath}': {e}")
        return False
    except Exception as e:
        # Catch-all for unexpected issues
        logger.error(f"Unexpected error writing to JSONL file '{filepath}': {e}")
        return False


def write_json_file(filepath: str, data: dict, cls=None) -> bool:
    """
    Write data to a JSON file with optional custom serialization.
    Args:
        filepath (str): The path where the JSON file will be written.
        data (dict): The dictionary containing data to be serialized and written to the file.
        cls (optional): A custom encoder class or serializer. If None, data is written directly.
                        If provided, objects with 'model_dump' method are serialized using it.
    Returns:
        bool: True if the file was written successfully, False otherwise.
    Raises:
        FileNotFoundError: If the directory path does not exist for the specified filepath.
        IOError: If the file cannot be written to the specified filepath.
        TypeError: If data cannot be serialized to JSON format.
        Generic Exception: Catches any other unexpected exceptions that may occur during file writing or serialization.
    Example:
        >>> write_json_file('output.json', {'key': 'value'})
        >>> write_json_file('output.json', {'obj': my_pydantic_model}, cls=CustomEncoder)
    """
    try:
        # Prepare the data
        if cls is None:
            serialized_data = data
        else:
            serialized_data = {
                key: val.model_dump() if hasattr(val, 'model_dump') else val 
                for key, val in data.items()
            }
            
        # Write to the file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(serialized_data, f, indent=2)
            
        return True
            
    except FileNotFoundError as e:
        # Happens if the directory path doesn't exist
        logger.error(f"Directory does not exist for output file '{filepath}': {e}")
        return False
    except IOError as e:
        # Happens on permission errors or disk full
        logger.error(f"Could not write to file '{filepath}': {e}")
        return False
    except TypeError as e:
        # Happens if the data contains an object that json.dump() cannot serialize
        logger.error(f"Data serialization error for '{filepath}': {e}")
        return False
    except Exception as e:
        # Catch-all for unexpected issues
        logger.error(f"Unexpected error writing JSON to '{filepath}': {e}")
        return False