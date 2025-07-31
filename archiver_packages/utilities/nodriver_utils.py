import nodriver as uc
import os
from time import sleep
from typing import Callable
from psutil import process_iter
from random import uniform

def kill_process(process_name: str) -> None:
    """Kill a process by name."""
    if process_name in (p.name() for p in process_iter()):
        os.system(f"taskkill /f /im {process_name}")

async def nodriver_setup(profile:str, browser:str, headless: bool):

    pc_user = os.getlogin()
    
    if browser == "Brave":
        program_files = "Program Files" if "BraveSoftware" in os.listdir("C:\\Program Files") else "Program Files (x86)"
        user_data_dir=rf"C:\Users\{pc_user}\AppData\Local\BraveSoftware\Brave-Browser\User Data"
        browser_executable_path=f"C:\\{program_files}\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
        process_name = "brave.exe"
    elif browser == "Chrome":
        program_files = "Program Files" if "Google" in os.listdir("C:\\Program Files") else "Program Files (x86)"
        user_data_dir=rf"C:\Users\{pc_user}\AppData\Local\Google\Chrome\User Data"
        browser_executable_path=f"C:\\{program_files}\\Google\\Chrome\\Application\\chrome.exe"
        process_name = "chrome.exe"
    elif browser == "Edge":
        program_files = "Program Files" if "Edge" in os.listdir("C:\\Program Files\\Microsoft") else "Program Files (x86)"
        user_data_dir=rf"C:\Users\{pc_user}\AppData\Local\Microsoft\Edge\User Data"
        browser_executable_path=f"C:\\{program_files}\\Microsoft\\Edge\\Application\\msedge.exe"
        process_name = "msedge.exe"
    else:
        print("Invalid browser name")
        return

    # Kill all chrome.exe processes to avoid chromedriver window already closed exception
    kill_process(process_name)

    driver = await uc.start(
        headless=headless,
        user_data_dir=user_data_dir, # by specifying it, it won't be automatically cleaned up when finished
        browser_executable_path=browser_executable_path,
        browser_args=[
            f'--profile-directory={profile}',
            "--mute-audio",
            "--disable-notifications",
            "--no-first-run",
            "--no-service-autorun",
            "--password-store=basic",
            "--hide-crash-restore-bubble",
            ],
        lang="en-US"
    )
    return driver

async def split_window_size(tab: uc.Tab, delay: Callable[[int], float]) -> None:
    """Split the window size."""
    await tab.set_window_size(top=1, left=1)
    sleep(delay())

async def get_nodriver_tab(driver, url: str, delay: Callable[[int], float], add_tab_delay: int = 5, split_tabs: bool = False) -> uc.Tab:
    """Get a new tab in the nodriver instance."""
    tab = await driver.get(url)
    sleep(delay() + add_tab_delay)
    if split_tabs:
        await split_window_size(tab, delay)
    return tab

async def slow_scroll(tab, delay: Callable[[int], float]) -> None:
    """Scroll the page slowly."""
    for _ in range(3):
        scroll_amount = uniform(100, 120)
        await tab.evaluate(f"window.scrollBy(0, {scroll_amount});")
        sleep(delay() + 1)

async def page_scroll(tab, delay: Callable[[int], float], add_delay: int = 0, end_key: bool = False) -> str | None:
    """Scroll the webpage. Return 'page_end' if reached the bottom."""
    last_height = await tab.evaluate("document.body.scrollHeight")
    sleep(delay() + 5 + add_delay)

    if end_key:
        await send_key(tab, "End", 35)
    else:
        await tab.evaluate("""
            var scrollingElement = document.scrollingElement || document.body;
            scrollingElement.scrollTop = scrollingElement.scrollHeight;
        """)

    new_height = await tab.evaluate("document.body.scrollHeight")

    if new_height == last_height: 
        return "page_end"

    last_height = new_height

async def page_scroll_to_bottom(tab, delay: Callable[[int], float], max_page_end_count: int = 5, page_scroll_limit: int = None, end_key: bool = False):
    """Scroll to the bottom of the page."""
    page_end_count = 0
    page_scroll_count = 0

    while True:
        page_scroll_count += 1
        if page_scroll_limit and page_scroll_count == page_scroll_limit:
                break

        if await page_scroll(tab, delay, end_key=end_key) == "page_end":
            page_end_count += 1
            if page_end_count > max_page_end_count:
                break
        else:
            page_end_count = 0

async def scroll_until_elements_loaded(tab, number_of_elements: int, number_of_page_results: int, delay: Callable[[int], float], extra_scrolls: int = 3):
    """Scroll to the bottom of the page until the desired number of elements are displayed."""
    scroll_count = max(1, (number_of_elements + number_of_page_results - 1) // number_of_page_results)
    scroll_count += extra_scrolls
    for _ in range(scroll_count):
        await send_key(tab, "End", 35)
        sleep(delay() + 1)

async def send_key(tab, key: str, windows_virtual_key_code: int, modifiers=None):
    """Send a key to the tab."""
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

async def send_key_element(self, key: str, windows_virtual_key_code: int) -> None:
    """Send a key event to a specific element."""
    await self.apply("(elem) => elem.focus()")
    await self.tab.send(uc.cdp.input_.dispatch_key_event(
        type_="keyDown",  # Press down the key
        key=key,
        code=key,
        windows_virtual_key_code=windows_virtual_key_code,
    ))
    await self.tab.send(uc.cdp.input_.dispatch_key_event(
        type_="keyUp",
        key=key,
        code=key,
        windows_virtual_key_code=windows_virtual_key_code,
    ))

async def nodriver_send_message(tab, message_input_ele, message: str, delay: Callable[[int], float], press_enter: bool = True):
    """Send a message in the nodriver instance."""
    messages: list[str] = message.split("\n")

    for idx, message in enumerate(messages):
        await message_input_ele.send_keys(message)

        # Only press Shift+Enter if it's not the last message
        if idx < len(messages) - 1:
            await send_key(tab, "Enter", 13, modifiers=8)

        sleep(delay())

    if press_enter:
        await send_key(tab, "Enter", 13)
        sleep(delay() + 3)

async def activate_dialog_window(element, delay: Callable[[int], float]) -> None:
    """Activate the dialog window to then scroll it down."""
    await element.mouse_click(button="middle")
    sleep(delay() + 2)

def random_delay(min_delay: int = 1) -> Callable[[int], float]:
    """Return a delay function with randomization."""
    return lambda delay=min_delay: uniform(delay, delay + 3)
