# Utility functions for the main archiver logic
import os
import re
from archiver_packages.utilities.utilities import clear
from datetime import datetime


def create_directory_with_timestamp() -> str:
    """Create a new directory with a timestamp in its name."""
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    new_directory_name = f"youtube_downloads ({current_time})"
    os.makedirs(new_directory_name, exist_ok=True)
    return new_directory_name


def chrome_version_exception(exception: str) -> None:
    """Display a Chrome version mismatch error and exit."""
    chromedriver_version_index = exception.find("Chrome version ")
    chromedriver_version = exception[chromedriver_version_index + len("Chrome version "):].split()[0]
    browser_version_index = exception.find("Current browser version is ")
    browser_version = exception[browser_version_index + len("Current browser version is "):].split()[0]
    title = "Chrome Version Mismatch"
    text = (
        f"Your current Google Chrome version is {browser_version}. For compatibility, "
        f"please uninstall the current version and install Chrome version {chromedriver_version}."
    )
    clear()
    print(f"\n{title}\n{text}")
    input("\nPress enter to exit")
    exit()


def rename_filename_to_id(filename_without_extension: str, html_dir: str, file_output_dir: str) -> str:
    """Rename a file to use its ID as the filename."""
    match = re.search(r'\[([a-zA-Z0-9_-]+)\]', filename_without_extension)
    if not match:
        return file_output_dir
    file_id = match.group(1)
    new_filename = f"{html_dir}/{file_id}.mp4"
    os.rename(file_output_dir, new_filename)
    return new_filename