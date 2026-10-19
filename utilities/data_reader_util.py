"""Utilities for loading test data from JSON, CSV, and Excel files."""

import csv
import json
from os import PathLike
from typing import Any, Optional, Union

import openpyxl

DataRow = tuple[Any, ...]
FilePath = Union[str, PathLike[str]]


def read_json_data(file_path: FilePath) -> list[DataRow]:
    """Read a JSON list of objects and return each object's values as a tuple."""
    with open(file_path, "r", encoding="utf-8") as file:
        json_data = json.load(file)

    if not isinstance(json_data, list):
        raise ValueError("JSON test data must contain a list of objects.")

    if not json_data:
        return []

    if not all(isinstance(record, dict) for record in json_data):
        invalid_index = next(
            index
            for index, record in enumerate(json_data, start=1)
            if not isinstance(record, dict)
        )
        raise ValueError(f"JSON record {invalid_index} must be an object.")

    keys = tuple(json_data[0])
    data: list[DataRow] = []
    for index, record in enumerate(json_data, start=1):
        if record.keys() != json_data[0].keys():
            raise ValueError(f"JSON record {index} has inconsistent fields.")
        data.append(tuple(record[key] for key in keys))

    return data


def read_csv_data(file_path: FilePath) -> list[DataRow]:
    """Read a CSV file and return each data row as a tuple, excluding headers."""
    with open(file_path, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        return [tuple(row.values()) for row in reader]


def read_excel_data(
    file_path: FilePath, sheet_name: Optional[str] = None
) -> list[DataRow]:
    """Read rows after the header from an Excel worksheet."""
    workbook = openpyxl.load_workbook(file_path, read_only=True)
    try:
        sheet = workbook[sheet_name] if sheet_name else workbook.active
        if sheet is None:
            raise ValueError("The Excel workbook does not contain an active worksheet.")

        return [
            row
            for row in sheet.iter_rows(min_row=2, values_only=True)
        ]
    finally:
        workbook.close()
