import nodriver as uc
from time import sleep
import os
from typing import Callable
from psutil import process_iter
from random import uniform



def kill_process(process_name:str):
    if process_name in (p.name() for p in process_iter()):
        os.system(f"taskkill /f /im  {process_name}")


async def nodriver_setup(profile:str):

    program_files = "Program Files" if "Google" in os.listdir("C:\\Program Files") else "Program Files (x86)"
    pc_user = os.getlogin()

    # Kill all chrome.exe processes to avoid chromedriver window already closed exception
    kill_process("chrome.exe")

    driver = await uc.start(
        headless=False,
        user_data_dir=rf"C:\Users\{pc_user}\AppData\Local\Google\Chrome\User Data",  # by specifying it, it won't be automatically cleaned up when finished
        browser_executable_path=f"C:\\{program_files}\\Google\\Chrome\\Application\\chrome.exe",
        browser_args=[
            f'--profile-directory={profile}',
            "--mute-audio",
            "--disable-notifications"
            ],
        lang="en-US"
    )
    return driver


async def split_window_size(tab:uc.Tab,delay:Callable[[int],float]):
    await tab.set_window_size(top=1, left=1)
    sleep(delay())


async def get_nodriver_tab(driver,url:str,delay:Callable[[int],float],add_tab_delay:int=5,split_tabs:bool=False) -> uc.Tab:

    tab = await driver.get(url)
    sleep(delay()+add_tab_delay)

    if split_tabs:
        await split_window_size(tab,delay)

    return tab


async def slow_croll(tab,delay:Callable[[int],float]):
    for _ in range(3):
        scroll_amount = uniform(100,120)
        await tab.evaluate(f"window.scrollBy(0, {scroll_amount});")
        sleep(delay()+1)


async def page_scroll(tab,delay:Callable[[int],float],add_delay:int=0,end_key:bool=False) -> str|None:
    '''Scroll the webpage. return str if reached to the bottom'''

    # Get old scroll position
    last_height = await tab.evaluate("document.body.scrollHeight")

    # Wait and scroll
    sleep(delay()+5+add_delay)

    if end_key:
        await send_key(tab, "End", 35)
    else:
        await tab.evaluate("""
            var scrollingElement = document.scrollingElement || document.body;
            scrollingElement.scrollTop = scrollingElement.scrollHeight;
        """)

    # # Scroll down the page by a random amount
    # scroll_amount = random.uniform(5, 100)
    # await tab.evaluate(f"window.scrollBy(0, {scroll_amount});")

    # Get the new scroll height
    new_height = await tab.evaluate("document.body.scrollHeight")

    if new_height == last_height: 
        return "page_end"

    # Update the last height for the next iteration
    last_height = new_height


async def page_scroll_to_bottom(tab,delay:Callable[[int],float],max_page_end_count:int=5,page_scroll_limit:int=None,end_key:bool=False):
    """ Scroll to the bottom of the page. """

    page_end_count = 0
    page_scroll_count = 0

    while True:
        page_scroll_count += 1

        if page_scroll_limit:
            if page_scroll_count == page_scroll_limit:
                break

        if await page_scroll(tab,delay,end_key=end_key) == "page_end":
            page_end_count += 1
            if page_end_count > max_page_end_count:
                break
        else:
            page_end_count = 0


async def scroll_until_elements_loaded(tab,number_of_elements:int,number_of_page_results:int,delay:Callable[[int],float],extra_scrolls:int=3):
    """
    Scrolls to the bottom of the page until the desired number of button elements are displayed.

    Parameters:
    - tab: The browser tab object.
    - number_of_elements: The total number of button elements to be displayed after scrolling.
    - number_of_page_results: The number of results displayed per scroll.

    Returns:
    - None
    """

    # Ensure at least required scrolls
    scroll_count = max(1, (number_of_elements + number_of_page_results - 1) // number_of_page_results)

    # Add extra page scrolls
    scroll_count = scroll_count + extra_scrolls

    for _ in range(scroll_count):
        await send_key(tab, "End", 35)
        sleep(delay()+1)


async def send_key(tab,key:str,windows_virtual_key_code:int,modifiers=None):
    """ Send a key to the tab. """

    # Dispatch the key event
    await tab.send(uc.cdp.input_.dispatch_key_event(
        type_="keyDown",  # Press down the key
        modifiers=modifiers,
        key=key,
        code=key,
        windows_virtual_key_code=windows_virtual_key_code,
    ))
    await tab.send(uc.cdp.input_.dispatch_key_event(
        type_="keyUp",  # Release the key
        modifiers=modifiers,
        key=key,
        code=key,
        windows_virtual_key_code=windows_virtual_key_code,
    ))


async def send_key_element(self,key:str,windows_virtual_key_code:int):
    await self.apply("(elem) => elem.focus()")

    # Dispatch the key event
    await self.tab.send(uc.cdp.input_.dispatch_key_event(
        type_="keyDown",  # Press down the key
        key=key,
        code=key,
        windows_virtual_key_code=windows_virtual_key_code,
    ))
    await self.tab.send(uc.cdp.input_.dispatch_key_event(
        type_="keyUp",  # Release the key
        key=key,
        code=key,
        windows_virtual_key_code=windows_virtual_key_code,
    ))


async def nodriver_send_message(tab,message_input_ele,message:str,delay:Callable[[int],float],press_enter:bool=True):

    messages:list[str] = message.split("\n")

    for idx, message in enumerate(messages):
        await message_input_ele.send_keys(message)

        # Only press Shift+Enter if it's not the last message
        if idx < len(messages) - 1:
            await send_key(tab, "Enter", 13, modifiers=8)

        sleep(delay())

    if press_enter:
        await send_key(tab,"Enter",13)
        sleep(delay()+3)


async def activate_dialog_window(element,delay:Callable[[int],float]):
    """ Activate the dialog window in order to then scroll it down"""

    await element.mouse_click(button="middle")
    sleep(delay()+2)


def random_delay(min_delay:int) -> float:
    from random import uniform
    delay = lambda delay = min_delay: uniform(delay,delay+3)
    return delay
