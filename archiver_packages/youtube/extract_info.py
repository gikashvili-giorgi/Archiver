from time import sleep
from archiver_packages.utilities.nodriver_utils import slow_scroll, get_nodriver_tab
from archiver_packages.utilities.file_utils import download_file
from typing import Callable
from bs4 import BeautifulSoup


async def scrape_info(driver, yt_link: str, delay: Callable[[int], float], split_tabs: bool) -> tuple:
    """Scrape YouTube video info and profile image.

    Args:
        driver: The web driver instance.
        yt_link (str): The YouTube video link.
        delay (Callable[[int], float]): A callable to introduce delay.
        split_tabs (bool): Whether to split tabs.
    """
    tab = await get_nodriver_tab(
        driver=driver,
        url=yt_link,
        delay=delay,
        add_tab_delay=3,
        split_tabs=split_tabs
    )

    await slow_scroll(tab, delay)
    sleep(delay() + 5)

    try:
        profile_image_ele = await tab.select('yt-img-shadow#avatar')
        await profile_image_ele.scroll_into_view()
        sleep(delay() + 1)
    except:
        pass

    driver_page_source = await tab.get_content()
    soup = BeautifulSoup(driver_page_source, 'html.parser')

    profile_image_node = soup.select_one('yt-img-shadow#avatar img')
    profile_image = profile_image_node.get("src") if profile_image_node else ""
    profile_image = profile_image.replace("s88-c-k", "s48-c-k") if profile_image else ""

    if not profile_image:
        print(f"Profile image not found for video: {yt_link}")

    comments_count_ele = soup.select_one('#comments')
    if comments_count_ele:
        comments_count_ele_text = comments_count_ele.get_text()
        if "Comments are turned off" in comments_count_ele_text:
            comments_status = False
        else:
            comments_status = True
    else:
        comments_status = True

    return tab, profile_image, comments_status

def download_youtube_thumbnail(info: dict, save_path: str) -> None:
    """Download the YouTube video thumbnail if available.

    Args:
        info (dict): The information dictionary containing the thumbnail URL.
        save_path (str): The path to save the downloaded thumbnail.
    """
    thumbnail_url = info.get('thumbnail')
    if thumbnail_url:
        download_file(thumbnail_url, save_path)