
import json
from collections.abc import Iterator

import ijson
import utils.log_manager as log_manager
from schemas import TestCase, TurnResult

logger = log_manager.get_logger(__name__)


def stream_json_file(filepath: str, prefix: str = "test_cases.item") -> Iterator[TestCase]:
    """
    Streams JSON objects from a file and yields them as TestCase instances.

    Args:
        filepath (str): The path to the JSON file containing test cases.
        prefix (str, optional): The ijson prefix path to iterate over items. Defaults to "test_cases.item".

    Yields:
        TestCase: TestCase objects parsed from each item in the JSON file.

    Raises:
        Logs and continues on Pydantic validation or parsing errors for individual items.
        Logs and returns if there are JSON file errors (structure, not found, I/O).

    Notes:
        - Uses incremental parsing for large files (via ijson).
        - Each yielded object is validated and loaded as a TestCase.
        - Logs detailed errors for invalid items or file issues without stopping iteration.
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
    Appends a single TurnResult instance as a JSON string to a file, creating or continuing a JSON Lines (JSONL) file.

    Args:
        filepath (str): The path to the JSONL file where the TurnResult will be appended.
        data (TurnResult): The TurnResult object to serialize and write as a single JSON line.

    Returns:
        bool: True if the data is successfully serialized and written to the file; False otherwise.

    Notes:
        - Each call writes one turn result as a single line (JSON object) to the file.
        - The function handles serialization using the Pydantic `model_dump()` method of TurnResult.
        - Returns False and logs an error in case of serialization, file system, or IO errors.
        - If the file or its parent directory does not exist, an error is logged and False is returned.

    Example:
        >>> success = append_to_jsonl("tester/data/report_raw.jsonl", turn_result)
        >>> if success:
        ...     print("Result appended to JSONL file.")
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