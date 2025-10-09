"""JSON utility functions for reading and writing JSON files with proper error handling.

This module provides robust JSON file operations with consistent error handling,
UTF-8 encoding support, and flexible formatting options.
"""

import json
from pathlib import Path
from typing import Any


def write_json_file(file_path: Path, data: Any, compact: bool = True) -> bool:
    """
    Write JSON data to a file with proper error handling.

    Args:
        file_path: Path to the JSON file
        data: Data to write (must be JSON serializable)
        compact: If True, writes compact JSON without whitespace.
                If False, writes pretty-printed JSON with 4-space indentation.

    Returns:
        bool: True if successful, False if failed

    Side Effects:
        - Creates or overwrites the file at file_path
        - Prints error message on failure

    Note:
        - Uses UTF-8 encoding for all files
        - Compact format uses separators (',', ':') without spaces
        - Pretty format uses 4-space indentation for readability

    Example:
        >>> write_json_file(Path('config.json'), {'key': 'value'}, compact=False)
        True
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            if compact:
                json.dump(data, f, separators=(",", ":"))
            else:
                json.dump(data, f, indent=4)
        return True
    except Exception as e:
        print(f"Error writing JSON file {file_path}: {e}")
        return False


def read_json_file(file_path: Path) -> dict[str, Any]:
    """
    Read JSON data from a file with proper error handling.

    Args:
        file_path: Path to the JSON file to read

    Returns:
        dict[str, Any]: The parsed JSON data

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON

    Side Effects:
        - Prints descriptive error messages before re-raising exceptions

    Note:
        - Uses UTF-8 encoding for reading files
        - Returns the parsed JSON as a dictionary
        - Does not suppress exceptions - caller must handle them

    Example:
        >>> data = read_json_file(Path('config.json'))
        >>> print(data['key'])
        'value'
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Configuration file {file_path} not found")
        raise
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in configuration file: {e}")
        raise

    # try:
    #     with open(file_path, "r", encoding="utf-8") as f:
    #         return json.load(f)
    # except Exception as e:
    #     print(f"Error reading JSON file {file_path}: {e}")
    #     return None


if __name__ == "__main__":
    # Example usage
    test_data = {"name": "Test", "value": 42, "items": [1, 2, 3]}

    # Write compact JSON
    success = write_json_file(Path("test_compact.json"), test_data)
    print(f"Compact write {'succeeded' if success else 'failed'}")

    # Write pretty JSON
    success = write_json_file(Path("test_pretty.json"), test_data, compact=False)
    print(f"Pretty write {'succeeded' if success else 'failed'}")

    # Read JSON
    data = read_json_file(Path("test_compact.json"))
    print(f"Read data: {data}")
