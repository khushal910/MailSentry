from __future__ import annotations
import os
import pickle
import yaml
from src.exception import MyException
from pathlib import Path

def read_yaml_file(file_path: str | Path) -> dict:
    """
    Reads a YAML file and returns its contents as a dictionary.

    Args:
        file_path (str | Path): Path to the YAML file.

    Returns:
        dict: Parsed YAML content.
    """

    file_path = Path(file_path)

    with open(file_path, "r", encoding="utf-8") as yaml_file:
        content = yaml.safe_load(yaml_file)

    return content


def read_csv(file_path: str | Path):
    """
    Reads a CSV file and returns its contents as a DataFrame.

    Args:
        file_path (str | Path): Path to the CSV file.
        
    Returns:
        DataFrame: Parsed CSV content.
    """
    import pandas as pd

    file_path = Path(file_path)

    dataframe = pd.read_csv(file_path)

    return dataframe
