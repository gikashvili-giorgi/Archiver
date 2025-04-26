import os
import json
import logging
import nodriver as uc
from archiver_packages.utilities.nodriver_utils import nodriver_setup, random_delay
from archiver_packages.utilities.file_utils import (
    move_file,
    create_directory,
    list_files_by_creation_date,
    extract_filename_without_extension,
)
from archiver_packages.youtube.download_video import (
    download_videos_with_info,
    get_youtube_links_from_playlist_and_channel,
    input_youtube_links,
)
from archiver_packages.utilities.archiver_utils import (
    create_directory_with_timestamp,
    chrome_version_exception,
    rename_filename_to_id,
)
from archiver_packages.youtube.youtube_to_html import parse_to_html

logging.basicConfig(level=logging.INFO)


def load_settings() -> dict:
    """Load settings from settings.json file."""
    with open("settings.json", encoding="utf-8") as f:
        return json.load(f)


async def archiver(
    yt_urls: list[str],
    test_code: bool = False,
    test_comments: int = None,
    test_headless: bool = False,
    test_profile: str = None,
    skip_download: bool = False,
) -> None:
    """
    Main archiver workflow: downloads videos, processes metadata, and generates HTML output.
    """
    settings = load_settings()
    save_comments = settings["youtube"]["save_comments"]
    max_comments = (
        test_comments if test_code and test_comments is not None else settings["youtube"]["max_comments"]
    )
    delay = random_delay(settings["extra"]["delay"])
    headless = test_headless if test_code and test_headless is not None else settings["extra"]["headless"]
    split_tabs = settings["extra"]["split_tabs"]
    profile = test_profile if test_code and test_profile is not None else settings["extra"]["profile"]

    output_directory = create_directory_with_timestamp()
    logging.info("Downloading videos...")

    # Extract yt urls from playlists and channels
    for yt_url in yt_urls[:]:
        if "&list=" in yt_url or "/@" in yt_url:
            extracted_urls = get_youtube_links_from_playlist_and_channel(yt_url)
            yt_urls.remove(yt_url)
            yt_urls.extend(extracted_urls)

    info_list = download_videos_with_info(yt_urls, output_directory, skip_download=skip_download)

    if test_code and skip_download:
        files = [""]
    else:
        files = list_files_by_creation_date(output_directory, except_extensions=[".json"])
        files_updated = []
        for file in files:
            filename_without_extension = extract_filename_without_extension(file)
            html_dir = f"{output_directory}/{filename_without_extension}"
            create_directory(html_dir)
            move_file(file, html_dir)
            file_output_dir = f"{html_dir}/{filename_without_extension}.mp4"
            file_output_dir = rename_filename_to_id(filename_without_extension, html_dir, file_output_dir)
            files_updated.append(file_output_dir)
            for f in os.listdir(output_directory):
                f_path = f"{output_directory}/{f}"
                if filename_without_extension in f and f.endswith(".json"):
                    move_file(f_path, html_dir)
        files = files_updated

    try:
        driver = await nodriver_setup(profile,headless)
    except Exception as e:
        logging.error(e)
        if "only supports Chrome version" in str(e):
            chrome_version_exception(str(e))
        return

    await parse_to_html(
        output_directory, yt_urls, files, info_list, driver, delay, save_comments, max_comments, split_tabs
    )
    driver.stop()
    logging.info("Completed.")


if __name__ == "__main__":
    yt_urls = input_youtube_links()
    uc.loop().run_until_complete(
        archiver(
            yt_urls,
        )
    )