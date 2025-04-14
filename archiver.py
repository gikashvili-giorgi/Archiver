import os, json
import nodriver as uc
from archiver_packages.utilities.nodriver_utils import nodriver_setup
from archiver_packages.utilities.nodriver_utils import random_delay
from archiver_packages.utilities.file_utils import move_file, create_directory, list_files_by_creation_date, extract_filename_without_extension
from archiver_packages.youtube.download_video import download_videos_with_info, get_youtube_links_from_playlist_and_channel, input_youtube_links
from archiver_packages.utilities.archiver_utils import create_directory_with_timestamp, chrome_version_exception, rename_filename_to_id
from archiver_packages.youtube.youtube_to_html import parse_to_html



async def archiver(yt_urls:list,test_code:bool=False,test_comments:int=None):

    # Load settings
    settings: dict = json.loads(open('settings.json', encoding="utf-8").read())

    save_comments = settings.get("youtube").get("save_comments")
    if test_code and test_comments is not None:
        max_comments = test_comments
    else:
        max_comments = settings.get("youtube").get("max_comments")
    delay = settings.get("extra").get("delay")
    delay = random_delay(delay)
    split_tabs = settings.get("extra").get("split_tabs")
    # headless = settings.get("extra").get("headless")

    output_directory = create_directory_with_timestamp()

    print("\nDownloading videos...")

    # Extract yt urls from playlists and channels
    for yt_url in yt_urls:
        if "&list=" in yt_url:
            extracted_urls = get_youtube_links_from_playlist_and_channel(yt_url)
            yt_urls.remove(yt_url)
            yt_urls.extend(extracted_urls)
        elif "/@" in yt_url:
            extracted_urls = get_youtube_links_from_playlist_and_channel(yt_url)
            yt_urls.remove(yt_url)
            yt_urls.extend(extracted_urls)

    # Download yt videos and extract metadata
    info_list = download_videos_with_info(yt_urls,output_directory,test_code=test_code)

    if test_code == True:
        files = [""]
    else:
        # List downloaded videos
        files = list_files_by_creation_date(output_directory,except_extensions=[".json"])
        files_updated = []

        # Move downloaded videos and info files to output folder
        for file in files:
            filename_without_extension = extract_filename_without_extension(file)
            html_dir = f"{output_directory}/{filename_without_extension}"
            create_directory(html_dir)
            move_file(file, html_dir)

            file_output_dir = f"{html_dir}/{filename_without_extension}.mp4"
            file_output_dir = rename_filename_to_id(filename_without_extension,html_dir,file_output_dir)

            files_updated.append(file_output_dir)

            # Move json files to html folder
            for file in os.listdir(output_directory):
                file = f"{output_directory}/{file}"
                if filename_without_extension in file and file.endswith(".json"):
                    move_file(file, html_dir)

        files = files_updated

    # Load chromedriver
    try:
        driver = await nodriver_setup(profile="Default")
    except Exception as e:
        print(e)

        if "only supports Chrome version" in e:
            chrome_version_exception(e)

    # Parse extracted metadata to html
    await parse_to_html(output_directory,yt_urls,files,info_list,driver,delay,save_comments,max_comments,split_tabs,test_code=test_code)

    driver.stop()

    print("\nCompleted..")


if __name__ == '__main__':

    from test_code import test_code, test_comments, test_yt_urls

    if test_code:
        yt_urls = test_yt_urls
    else:
        yt_urls = input_youtube_links()

    uc.loop().run_until_complete(
        archiver(
            yt_urls,
            test_code=test_code,
            test_comments=test_comments
        )
    )