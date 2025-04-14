from selectolax.parser import HTMLParser
from time import sleep
from archiver_packages.utilities.selenium_utils import slow_croll
from archiver_packages.utilities.nodriver_utils import get_nodriver_tab
from archiver_packages.utilities.file_utils import download_file
from typing import Callable



async def scrape_info(driver,yt_link:str,delay:Callable[[int],float],split_tabs:bool) -> str:

    tab = await get_nodriver_tab(
        driver=driver,
        url=yt_link,
        delay=delay,
        add_tab_delay=2,
        split_tabs=split_tabs
        )

    await slow_croll(tab,delay) # Scroll to description section
    sleep(delay()+2)

    driver_page_source = await tab.get_content()
    html = HTMLParser(driver_page_source, detect_encoding=True)

    profile_image = html.css_first('yt-img-shadow#avatar img').attributes.get("src")
    profile_image = "".join(profile_image.replace("s88-c-k", "s48-c-k")) # Make profile img size 48x48

    return tab, profile_image


def download_youtube_thumbnail(info:dict,save_path:str):
    thumbnail_url = info.get('thumbnail')
    if thumbnail_url:
        download_file(thumbnail_url, save_path)