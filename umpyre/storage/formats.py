"""JSON and CSV serialization for metrics."""

import json
import csv
from pathlib import Path
from typing import Any
from io import StringIO


def _serialize_json(data: dict, file_path: Path, indent: int = 2):
    """Serialize metrics to JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=indent, sort_keys=True)


def _deserialize_json(file_path: Path) -> dict:
    """Deserialize metrics from JSON file."""
    with open(file_path) as f:
        return json.load(f)


def _serialize_csv(data: dict, file_path: Path):
    """
    Serialize metrics to CSV file (flat format).

    Args:
        data: Nested metric dictionary
        file_path: Path to CSV file
    """
    # Flatten nested structure
    flat_data = _flatten_dict(data)

    with open(file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(['metric', 'value'])
        # Write data
        for key, value in flat_data.items():
            writer.writerow([key, value])


def _deserialize_csv(file_path: Path) -> dict:
    """
    Deserialize metrics from CSV file.

    Returns:
        Flat dictionary of metrics
    """
    data = {}
    with open(file_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data[row['metric']] = row['value']
    return data


def _flatten_dict(d: dict, parent_key: str = '', sep: str = '.') -> dict:
    """
    Flatten nested dictionary.

    Example:
        >>> _flatten_dict({'a': {'b': 1, 'c': 2}, 'd': 3})
        {'a.b': 1, 'a.c': 2, 'd': 3}
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def serialize_metrics(data: dict, output_path: Path, format: str = 'json'):
    """
    Serialize metrics to file.

    Args:
        data: Metric dictionary
        output_path: Path to output file
        format: Format ('json' or 'csv')
    """
    if format == 'json':
        _serialize_json(data, output_path)
    elif format == 'csv':
        _serialize_csv(data, output_path)
    else:
        raise ValueError(f"Unsupported format: {format}")


def deserialize_metrics(file_path: Path, format: str = 'json') -> dict:
    """
    Deserialize metrics from file.

    Args:
        file_path: Path to input file
        format: Format ('json' or 'csv')

    Returns:
        Metric dictionary
    """
    if format == 'json':
        return _deserialize_json(file_path)
    elif format == 'csv':
        return _deserialize_csv(file_path)
    else:
        raise ValueError(f"Unsupported format: {format}")
