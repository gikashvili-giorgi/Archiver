import os, re
import logging
import traceback
from archiver_packages.youtube.extract_info import (
    download_youtube_thumbnail,
    download_youtube_channel_avatar_image,
    download_youtube_channel_banner_image,
    get_channel_avatar_links,
    get_channel_banner_link,
)
from archiver_packages.youtube.add_comments import add_comments
from archiver_packages.utilities.utilities import convert_date_format
from archiver_packages.utilities.file_utils import copy_file_or_directory
from archiver_packages.utilities.nodriver_utils import get_nodriver_tab
from archiver_packages.youtube.download_video import download_best_audio
from typing import Callable
import archiver_packages.youtube_html_elements as youtube_html_elements


def get_comments_status(info: dict) -> bool:
    """Return whether yt-dlp found an available comments section.

    yt-dlp returns ``comments=None`` and ``comment_count=None`` when its
    comments extractor detects that comments are disabled.  An empty list is
    a valid enabled state for a video with no comments, so it must not be
    treated as disabled.
    """
    if "comments" not in info:
        logging.warning(
            "yt-dlp did not return comment extraction status; "
            "falling back to comment_count."
        )
        return info.get("comment_count") is not None

    return info["comments"] is not None


def modify_exctracted_info(yt_url: str, video_publish_date: str, channel_keywords: list, channel_description: str, like_count: int | None, dislike_count: int | None, comment_count: int, comments_status: bool) -> tuple:
    """
    Modify extracted YouTube video information.

    Args:
        yt_url (str): YouTube video URL.
        video_publish_date (str): Video publish date.
        channel_keywords (list): List of channel keywords.
        channel_description (str): Channel description.
        like_count (int | None): Number of likes.
        dislike_count (int | None): Number of dislikes.

    Returns:
        tuple: Modified YouTube video information.
    """
    # Remove timecode from video URL
    if "&" in yt_url:
        yt_url = yt_url.split("&")[0]

    # Modify date format
    video_publish_date = convert_date_format(video_publish_date)

    # Add hashtag to keyword tags
    channel_keywords = ['#' + i for i in channel_keywords]
    channel_keywords = ' '.join(channel_keywords)

    # Make description link-clickable
    channel_description = re.sub(r'http\S+', '<a href="' + "\\g<0>" + '">' + "\\g<0>" + '</a>', channel_description)

    # Make hashtags clickable
    description_hashtags = re.findall(r"#\w+", channel_description)
    for description_hashtag in description_hashtags:
        hashtag_url = "https://www.youtube.com/hashtag/" + description_hashtag.lower()[1:]
        hashtag = youtube_html_elements.redirect_url(description_hashtag, hashtag_url)
        channel_description = channel_description.replace(description_hashtag, hashtag)

    # Make description timestamp clickable
    description_timestamps = re.findall(r'(?<!\d)(\d+:\d{2})\b', channel_description)
    for description_timestamp in description_timestamps:
        # Convert to seconds
        minutes, seconds = map(int, description_timestamp.split(':'))
        description_timestamp_in_seconds = minutes * 60 + seconds

        timestamp_url = yt_url + f"&t={description_timestamp_in_seconds}s"
        timestamp = youtube_html_elements.redirect_url(description_timestamp, timestamp_url)
        channel_description = channel_description.replace(description_timestamp, timestamp)

    # Add likes
    if like_count is not None:
        like_count = f'{like_count:,}'
    else:
        like_count = "LIKE"

    # Add dislikes
    if dislike_count is not None:
        dislike_count = f'{dislike_count:,}'
    else:
        dislike_count = "DISLIKE"

    # Add comments tag
    if comments_status:
        comment_count_html_str = f"{comment_count:,} Comments"
    else:
        comment_count_html_str = "Comments are turned off."

    return (yt_url, video_publish_date, channel_keywords, channel_description, like_count, dislike_count, comment_count_html_str)


def get_html_output_dir(video_id: str, root_directory: str) -> str | None:
    """
    Get the HTML output directory for a given video ID.

    Args:
        video_id (str): YouTube video ID.
        root_directory (str): Root directory to search in.

    Returns:
        str | None: HTML output directory, or None if not found.
    """
    for dir in os.listdir(root_directory):
        if video_id in dir:
            return os.path.join(root_directory, dir)
    logging.error(f"No directory found for video_id: {video_id} in {root_directory}")
    return None


def move_files_with_extension(src_dir: str, ext: str, dest_folder: str) -> None:
    """
    Move files with a given extension from src_dir to dest_folder.
    Logs errors with tracebacks if any file move fails.
    """
    os.makedirs(dest_folder, exist_ok=True)
    for filename in os.listdir(src_dir):
        if filename.endswith(ext):
            src = os.path.join(src_dir, filename)
            dst = os.path.join(dest_folder, filename)
            try:
                os.rename(src, dst)
            except FileExistsError:
                logging.warning(f"File {dst} already exists. Skipping.")
            except Exception as e:
                logging.error(f"Error moving {src} to {dst}: {e}\n{traceback.format_exc()}")


async def parse_to_html(
    output_directory: str,
    yt_urls: list[str],
    files: list[str],
    info_list: list[dict],
    driver,
    delay: Callable[[int], float],
    save_comments: bool,
    max_comments: int,
    split_tabs: bool,
    webdriver_comment_extractor: bool = False,
) -> None:
    """
    Parse YouTube video information to HTML.

    Args:
        output_directory (str): Directory to save the HTML export directories.
        yt_urls (list[str]): List of YouTube URLs.
        files (list[str]): List of file paths.
        info_list (list[dict]): List of video information dictionaries.
        driver: Optional web driver instance. It is only used by the
            webdriver comment extractor.
        delay (Callable[[int], float]): Delay function.
        save_comments (bool): Whether to save comments.
        max_comments (int): Maximum number of comments to save.
        split_tabs (bool): Whether to split tabs.
        webdriver_comment_extractor (bool): Use nodriver instead of
            youtube-comment-downloader for comment extraction.
    """
    for (yt_url, file, info) in zip(yt_urls, files, info_list):
        filename = os.path.basename(file)
        # Extract the relevant pieces of information
        video_title = info.get('title', None)
        video_views = info.get('view_count', None)
        video_views = "" if video_views is None else f'{video_views:,}'
        channel_author = info.get('uploader', None)
        channel_url = info.get('uploader_url', None)
        channel_url = "Channel URL not found" if channel_url is None else channel_url
        video_publish_date = info.get('upload_date', None)
        channel_keywords = info.get('tags', None)
        channel_description = info.get('description', None)
        subscribers = info.get('channel_follower_count', None)
        subscribers = "" if subscribers is None else f'{subscribers:,} subscribers'
        like_count = info.get('like_count', None)
        dislike_count = info.get('dislike_count', None)
        comment_count = info.get('comment_count', None)
        comment_count = 0 if comment_count is None else comment_count
        comments_status = get_comments_status(info)
        video_id = info.get("id")
        thumbnail_url = info.get('thumbnail')
        # Get the HTML output directory for the video
        html_output_directory = get_html_output_dir(video_id, output_directory)
        if html_output_directory is None:
            logging.error(f"Skipping video {video_title} due to missing output directory.")
            continue
        try:
            images_output_directory = os.path.join(
                html_output_directory,
                "images-extracted",
            )
            os.makedirs(images_output_directory, exist_ok=True)

            # Download thumbnail
            download_youtube_thumbnail(
                thumbnail_url,
                os.path.join(images_output_directory, f"{video_id}_thumbnail.jpg"),
            )
            with open("./archiver_packages/youtube_html/index.html", 'rt', encoding="utf8") as input_file, \
                 open(f"{html_output_directory}/YouTube.html", 'wt', encoding="utf8") as output_file:

                # Extract the channel avatar
                channel_avatar_url_full, channel_avatar_url_small = get_channel_avatar_links(info)
                # Download the channel avatar
                download_youtube_channel_avatar_image(
                    channel_avatar_url_full,
                    os.path.join(
                        images_output_directory,
                        f"{video_id}_channel_avatar.jpg",
                    ),
                )
                # Extract and download the channel banner
                channel_banner_url = get_channel_banner_link(info)
                download_youtube_channel_banner_image(
                    channel_banner_url,
                    os.path.join(
                        images_output_directory,
                        f"{video_id}_channel_banner.jpg",
                    ),
                )
                tab = None
                if save_comments and comments_status and webdriver_comment_extractor:
                    if driver is None:
                        raise RuntimeError(
                            "A web driver is required for the webdriver comment extractor."
                        )
                    tab = await get_nodriver_tab(
                        driver=driver,
                        url=yt_url,
                        delay=delay,
                        add_tab_delay=3,
                        split_tabs=split_tabs,
                    )

                # Modify extracted info
                yt_url, video_publish_date, channel_keywords, channel_description, like_count, dislike_count, comment_count_html_str = modify_exctracted_info(
                    yt_url, video_publish_date, channel_keywords, channel_description, like_count, dislike_count, comment_count, comments_status)
                
                for line in input_file:
                    output_file.write(
                        line.replace('REPLACE_TITLE', video_title)
                        .replace('TITLE_URL', yt_url)
                        .replace('NUMBER_OF_VIEWS', video_views)
                        .replace('CHANNEL_AUTHOR', channel_author)
                        .replace('CHANNEL_URL', channel_url)
                        .replace('PUBLISH_DATE', f'{video_publish_date}')
                        .replace('CHANNEL_KEYWORDS', f'{channel_keywords}')
                        .replace('CHANNEL_DESCRIPTION', channel_description)
                        .replace('CHANNEL_SUBSCRIBERS', subscribers)
                        .replace('CHANNEL_AVATAR_URL', channel_avatar_url_small)
                        .replace('LIKE_COUNT', like_count)
                        .replace('DISLIKES_COUNT', dislike_count)
                        .replace('COMMENT_COUNT', comment_count_html_str)
                        .replace('VIDEO_SOURCE', f'media-extracted/{filename}')
                    )
                if save_comments and comments_status:
                    await add_comments(
                        tab,
                        html_output_directory,
                        channel_avatar_url_small,
                        comment_count,
                        channel_author,
                        output_file,
                        delay,
                        max_comments,
                        yt_url=yt_url,
                        webdriver_comment_extractor=webdriver_comment_extractor,
                    )
                output_file.write(youtube_html_elements.ending.html_end)
                logging.info(f"HTML file created for {video_title}")
        except Exception as e:
            logging.error(f"Error processing video {video_title}: {e}\n{traceback.format_exc()}")
            continue
        # Copy assets and styles folders to html output dir
        for folder in ["assets", "styles"]:
            try:
                copy_file_or_directory(
                    f"archiver_packages/youtube_html/{folder}",
                    html_output_directory
                )
            except Exception as e:
                logging.error(f"Error copying {folder} to {html_output_directory}: {e}\n{traceback.format_exc()}")
        # Move .json and .mp4 files using helper
        move_files_with_extension(html_output_directory, ".json", os.path.join(html_output_directory, "data-extracted"))
        move_files_with_extension(html_output_directory, ".mp4", os.path.join(html_output_directory, "media-extracted"))
        try:
            download_best_audio(yt_url, os.path.join(html_output_directory, "media-extracted"))
        except Exception as e:
            logging.error(f"Error downloading best audio for {video_title}: {e}\n{traceback.format_exc()}")
