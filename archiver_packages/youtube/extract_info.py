import logging
import yt_dlp

from archiver_packages.utilities.file_utils import download_file


_CHANNEL_THUMBNAILS_CACHE: dict[str, list[dict]] = {}


def _get_channel_thumbnails(info: dict) -> tuple[str, list[dict]]:
    """Extract and cache the channel thumbnails exposed by yt-dlp."""
    channel_url = info.get("channel_url") or info.get("uploader_url")
    if not channel_url:
        logging.warning("Channel URL not found; cannot extract channel images.")
        return "", []

    cache_key = str(info.get("channel_id") or channel_url)
    if cache_key in _CHANNEL_THUMBNAILS_CACHE:
        return channel_url, _CHANNEL_THUMBNAILS_CACHE[cache_key]

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "playlist_items": "0",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            channel_info = ydl.extract_info(channel_url, download=False)
    except Exception as exc:
        logging.warning("Could not extract channel images: %s", exc)
        return channel_url, []

    thumbnails = channel_info.get("thumbnails") or []
    _CHANNEL_THUMBNAILS_CACHE[cache_key] = thumbnails
    return channel_url, thumbnails


def get_channel_avatar_links(info: dict) -> tuple[str, str]:
    """Extract a channel avatar URL with yt-dlp.

    A video's metadata does not normally include the uploader avatar.  yt-dlp
    exposes it when the video's channel URL is extracted separately.  The
    result is cached so videos from the same channel do not trigger repeated
    channel requests.

    Args:
        info (dict): Video metadata returned by yt-dlp.

    Returns:
        str: The channel avatar URL, or an empty string when unavailable.
    """
    channel_url, thumbnails = _get_channel_thumbnails(info)
    if not channel_url:
        return "", ""

    channel_avatar_url = next(
        (
            thumbnail.get("url")
            for thumbnail in thumbnails
            if thumbnail.get("id") == "avatar_uncropped"
            and thumbnail.get("url")
        ),
        "",
    )

    if not channel_avatar_url:
        channel_avatar_url = next(
            (
                thumbnail.get("url")
                for thumbnail in thumbnails
                if "avatar" in str(thumbnail.get("id", "")).lower()
                and thumbnail.get("url")
            ),
            "",
        )

    channel_avatar_url_full, channel_avatar_url_small = "", ""

    if channel_avatar_url:
        channel_avatar_url = channel_avatar_url.split("=s")[0]
    else:
        logging.warning("Channel avatar URL not found for channel: %s", channel_url)

    if channel_avatar_url:
        channel_avatar_url_full = channel_avatar_url + "s0"
        channel_avatar_url_small = channel_avatar_url + "=s48-c-k-c0x00ffffff-no-rj"

    return channel_avatar_url_full, channel_avatar_url_small


def get_channel_banner_link(info: dict) -> str:
    """Extract the uncropped YouTube channel banner URL with yt-dlp."""
    channel_url, thumbnails = _get_channel_thumbnails(info)
    if not channel_url:
        return ""

    channel_banner_url = next(
        (
            thumbnail.get("url")
            for thumbnail in thumbnails
            if thumbnail.get("id") == "banner_uncropped"
            and thumbnail.get("url")
        ),
        "",
    )

    if not channel_banner_url:
        channel_banner_url = next(
            (
                thumbnail.get("url")
                for thumbnail in thumbnails
                if "banner" in str(thumbnail.get("id", "")).lower()
                and thumbnail.get("url")
            ),
            "",
        )

    if not channel_banner_url:
        logging.warning("Channel banner URL not found for channel: %s", channel_url)

    return channel_banner_url


def download_youtube_thumbnail(thumbnail_url: str, save_path: str) -> None:
    """Download the YouTube video thumbnail if available.

    Args:
        thumbnail_url (str): The URL of the YouTube video thumbnail to download.
        save_path (str): The path to save the downloaded thumbnail.
    """
    if thumbnail_url:
        download_file(thumbnail_url, save_path)


def download_youtube_channel_avatar_image(youtube_channel_avatar_url: str, save_path: str) -> None:
    """Download the YouTube channel avatar image.

    Args:
        youtube_channel_avatar_url (str): The URL of the YouTube channel avatar image to download.
        save_path (str): The path to save the downloaded channel avatar image.
    """
    if youtube_channel_avatar_url:
        download_file(youtube_channel_avatar_url, save_path)


def download_youtube_channel_banner_image(youtube_channel_banner_url: str, save_path: str) -> None:
    """Download the YouTube channel banner image."""
    if youtube_channel_banner_url:
        download_file(youtube_channel_banner_url, save_path)
