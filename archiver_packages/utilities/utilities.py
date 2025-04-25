# General utility functions for the archiver project
import os
from datetime import datetime
import logging


def clear() -> None:
    """
    Clear the terminal screen.
    """
    os.system('cls' if os.name=='nt' else 'clear')


def convert_date_format(input_date: str) -> str:
    """
    Convert a date string from 'YYYYMMDD' to 'DD Month YYYY'.

    Args:
        input_date (str): Date string in 'YYYYMMDD' format.

    Returns:
        str: Date string in 'DD Month YYYY' format.
    """
    try:
        parsed_date = datetime.strptime(input_date, "%Y%m%d")
        formatted_date = parsed_date.strftime("%d %B %Y")
        return formatted_date
    except ValueError as e:
        logging.error(f"Invalid date format: {input_date}. Error: {e}")
        return input_date