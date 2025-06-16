import logging
import traceback
import urllib.parse
import json
from time import sleep
from typing import Callable
from selectolax.parser import HTMLParser
from bs4 import BeautifulSoup
from archiver_packages.utilities.nodriver_utils import slow_croll, page_scroll, scroll_until_elements_loaded, activate_dialog_window
from archiver_packages.youtube.extract_comment_emoji import convert_youtube_emoji_url_to_emoji
import archiver_packages.youtube_html_elements as youtube_html_elements


logging.basicConfig(level=logging.INFO)


def format_text_emoji(input_text: str) -> str:
    """
    Format text with emojis, merging single-character lines with the previous line.

    Args:
        input_text (str): The input text to format.

    Returns:
        str: The formatted text.
    """
    lines = input_text.split('\n')
    merged_lines = []
    for i, line in enumerate(lines):
        if i > 0 and len(line) == 1:
            merged_lines[-1] += ' ' + line
        else:
            merged_lines.append(line)
    return '\n'.join(merged_lines)


async def parse_comment_text(comment_ele:HTMLParser) -> tuple[str, str]:
    """
    Parse comments/replies text and return both plain and styled text.

    Args:
        comment_ele: The comment element to parse.

    Returns:
        tuple[str, str]: Plain text and styled text.
    """
    text_ele = comment_ele.css_first('#content-text')
    text_ele_html = text_ele.html
    soup = BeautifulSoup(text_ele_html, 'html.parser')
    # Replace <img> tags with emoji
    for img_ele in soup.find_all(lambda tag: tag.name == "img" and tag.has_attr('src') and "emoji" in tag["src"]):
        emoji_url = img_ele["src"]
        emoji = convert_youtube_emoji_url_to_emoji(emoji_url)
        img_ele.replace_with(emoji)
    url_list, timestamp_list = [], []
    # Replace url tags with url
    for url_ele in soup.find_all(lambda tag: tag.name == "a" and tag.has_attr('href') and "https://" in tag.text):
        url = url_ele.text.strip()
        url_ele.replace_with(url)
        url_list.append(url)
    # Replace timestamp <a> tags with styled timestamp  
    for url_ele in soup.find_all(lambda tag: tag.name == "a" and tag.has_attr('href') and "&t=" in tag["href"]):
        timestamp_url = url_ele["href"]
        timestamp_url = "https://www.youtube.com/" + timestamp_url
        timestamp_text = url_ele.text.strip()
        url_ele.replace_with(timestamp_text)
        timestamp_list.append({"text": timestamp_text, "url": timestamp_url})
    # Extract text
    text = soup.get_text(separator=' ')
    styled_text = text
    # Replace url tags with styled urls
    for url in url_list:
        styled_url = youtube_html_elements.text_url_style(url)
        styled_text = styled_text.replace(url, styled_url)
    # Replace timestamp tags with styled timestamps
    for timestamp in timestamp_list:
        timestamp_text = timestamp.get("text")
        timestamp_url = timestamp.get("url")
        styled_timestamp = youtube_html_elements.redirect_url(timestamp_text, timestamp_url)
        styled_text = styled_text.replace(timestamp_text, styled_timestamp)
    return text, styled_text


def style_reply_mention(input_text: str) -> str:
    """
    Style reply mentions in the input text.

    Args:
        input_text (str): The input text to style.

    Returns:
        str: The styled text with mentions.
    """
    input_text = input_text.strip()
    if input_text.startswith('@'):
        words = input_text.split(' ', 1)
        if len(words) > 1:
            mention, remaining_text = words
            mention = mention.strip()
            input_text = youtube_html_elements.mention(mention)
            input_text = f"{input_text} {remaining_text}"
    return input_text


def parse_comments(html: HTMLParser) -> tuple[str, str, str, str, str]:
    """
    Parse comment HTML and extract like count, username, date, channel URL, and profile picture.

    Args:
        html (HTMLParser): The HTML parser object for the comment.

    Returns:
        tuple[str, str, str, str, str]: like_count, channel_username, comment_date, channel_url, channel_pfp
    """
    like_count = html.css_first("[id='vote-count-middle']").text().strip()
    channel_username = html.css_first("[id='author-text']").attributes.get("href")[1:]
    channel_username = urllib.parse.unquote(channel_username)
    comment_date = html.css_first("div[id='header-author'] span[id='published-time-text'] a").text().strip()
    channel_url = html.css_first("div[id='main'] div a").attributes.get("href")
    channel_url = "https://www.youtube.com" + channel_url
    channel_pfp = html.css_first("yt-img-shadow [id='img']").attributes.get("src")
    channel_pfp = channel_pfp.replace("s88-c-k", "s48-c-k")
    return like_count, channel_username, comment_date, channel_url, channel_pfp


async def load_all_comments(tab, delay: Callable[[int], float], max_comments: int, comment_count: int):
    """
    Scroll to end of the page to load all comments.

    Args:
        tab: The browser tab object.
        delay (Callable): Delay function.
        max_comments (int): Maximum number of comments to load.
        comment_count (int): Total number of comments expected.

    Returns:
        list: List of loaded comment elements.
    """
    sleep(delay() + 2)
    try:
        activate_btn = await tab.select("#owner-sub-count")
        await activate_dialog_window(activate_btn, delay)
    except:
        pass
    sleep(delay() + 2)
    await scroll_until_elements_loaded(
        tab=tab,
        number_of_elements=comment_count,
        number_of_page_results=20,
        delay=delay,
        extra_scrolls=5,
    )
    page_end_count = 0
    while True:
        if await page_scroll(tab, delay) == "page_end":
            page_end_count += 1
            if page_end_count > 3:
                break
            if page_end_count > 2:
                sleep(delay() + 1)
                await slow_croll(tab, delay)
        else:
            page_end_count = 0
        comments = await tab.select_all('#contents ytd-comment-thread-renderer')
        comments_count = len(comments)
        if comments_count > max_comments:
            break
    return comments


async def check_for_pinned_comment(comment:HTMLParser, comments_fetched: int) -> bool:
    """
    Check if the comment is pinned.

    Args:
        comment: The comment element.
        comments_fetched (int): Number of comments fetched so far.

    Returns:
        bool: True if the comment is pinned, False otherwise.
    """
    is_comment_pinned = False
    if comments_fetched == 1:
        pinned_comment_elements = comment.css("ytd-pinned-comment-badge-renderer")
        if len(pinned_comment_elements) > 0:
            is_comment_pinned = True
    return is_comment_pinned


def save_comments_to_json_file(path: str, comments_list: list[dict]) -> None:
    """
    Save comments to a JSON file.

    Args:
        path (str): Path to save the JSON file.
        comments_list (list[dict]): List of comment dictionaries.
    """
    if comments_list:
        try:
            data = json.dumps(comments_list, indent=4)
            with open(path, "w", encoding="utf-8") as outfile:
                outfile.write(data)
        except (OSError, TypeError) as e:
            logging.error(f"Error saving comments to {path}: {e}\n{traceback.format_exc()}")


async def expand_all_comments(tab, delay: Callable[[int], float]):
    """
    Expand all comments and replies on the page.

    Args:
        tab: The browser tab object.
        delay (Callable): Delay function.
    """
    logging.info("Expanding all comments...")
    expand_buttons = await tab.select_all('#more-replies button')
    for button in expand_buttons:
        await button.scroll_into_view()
        sleep(delay() + 1)
        await button.click()
        sleep(delay() + 2)
        await slow_croll(tab, delay)
        sleep(delay() + 2)
    while True:
        show_more_replies = await tab.select_all("button[aria-label='Show more replies']")
        if len(show_more_replies) == 0:
            break
        for button in show_more_replies:
            await button.scroll_into_view()
            sleep(delay() + 1)
            await button.click()
            sleep(delay() + 2)
            await slow_croll(tab, delay)
            sleep(delay() + 4)

async def add_comments(
    tab,
    output_directory: str,
    profile_image: str,
    comment_count: int,
    channel_author: str,
    output,
    delay: Callable[[int], float],
    max_comments: int
) -> None:
    """
    Fetch and process YouTube comments, saving them to HTML and JSON.

    Args:
        tab: The browser tab object.
        output_directory (str): Directory to save the output files.
        profile_image (str): URL of the profile image.
        comment_count (int): Total number of comments expected.
        channel_author (str): Author of the channel.
        output: Output file object.
        delay (Callable): Delay function.
        max_comments (int): Maximum number of comments to fetch.
    """
    await slow_croll(tab, delay)
    logging.info("Loading comments...")
    print("[DEBUG] Calling load_all_comments...")
    loaded_comments = await load_all_comments(tab, delay, max_comments, comment_count)
    print(f"[DEBUG] load_all_comments returned {len(loaded_comments) if loaded_comments else 0} elements")

    # Expand all comments and replies
    print("[DEBUG] Expanding all comments...")
    await expand_all_comments(tab, delay)

    #get html from tab
    print("[DEBUG] Getting HTML from tab...")
    tab_html = await tab.get_content()
    print(f"[DEBUG] tab.get_html() type: {type(tab_html)}, length: {len(tab_html) if tab_html else 'None'}")
    if not tab_html:
        print("[ERROR] tab.get_html() returned None or empty string!")
        logging.error("tab.get_html() returned None or empty string!")
        return
    #parse html with selectolax
    try:
        tab_html = HTMLParser(tab_html)
        print("[DEBUG] HTMLParser successfully parsed tab_html.")
    except Exception as e:
        print(f"[ERROR] HTMLParser failed: {e}\n{traceback.format_exc()}")
        logging.error(f"HTMLParser failed: {e}\n{traceback.format_exc()}")
        return
    # get all comments
    comments = tab_html.css('#contents ytd-comment-thread-renderer')
    print(f"[DEBUG] Found {len(comments)} comment elements in HTML.")
    if not comments:
        print("[ERROR] No comments found in HTML!")
        logging.error("No comments found in HTML!")
        return
    comments = comments[:max_comments]

    logging.info("Fetching comments...")
    print(f"[DEBUG] Processing up to {len(comments)} comments...")
    comments_count = len(comments)
    comments_fetched = 0
    comments_list = []
    try:
        for comment in comments:
            comments_fetched += 1
            logging.info(f"Fetched {comments_fetched}/{comments_count} comments.")
            print(f"[DEBUG] Processing comment {comments_fetched}/{comments_count}")
            is_comment_pinned = await check_for_pinned_comment(comment, comments_fetched)
            sleep(delay() + 1)
            text, styled_text = await parse_comment_text(comment)
            print(f"[DEBUG] Comment text: {text[:50]}...")
            like_count, channel_username, comment_date, channel_url, channel_pfp = parse_comments(comment)
            print(f"[DEBUG] like_count: {like_count}, channel_username: {channel_username}")
            heart = comment.css_first('#creator-heart-button')
            if heart:
                heart = youtube_html_elements.heart(profile_image)
            else:
                heart = ""
            comment_box = youtube_html_elements.comment_box(
                channel_url, channel_pfp, channel_username, channel_author, comment_date, styled_text, like_count, heart, is_comment_pinned
            )
            divs = youtube_html_elements.ending.divs
            author_heart = bool(heart)
            comment_dict = {
                "text": text,
                "like_count": like_count,
                "channel_username": channel_username,
                "comment_date": comment_date,
                "channel_url": channel_url,
                "channel_pfp": channel_pfp,
                "author_heart": author_heart,
                "replies": []
            }
            replies_btn = comment.css("#more-replies button")
            if len(replies_btn) == 0:
                comment_box += divs
                output.write(comment_box)
            else:
                reply_count = comment.css_first("[id='more-replies'] button")
                try:
                    reply_count = reply_count.attributes.get("aria-label")
                except Exception as ex:
                    logging.warning(f"Could not get aria-label for reply count: {ex}")
                    reply_count = reply_count.text()
                replies_toggle = youtube_html_elements.replies_toggle(reply_count)
                comment_box += replies_toggle + divs
                output.write(comment_box)
                sleep(delay())
                replies = comment.css('div[id="expander"] div[id="expander-contents"] #body')
                print(f"[DEBUG] Found {len(replies)} replies for comment {comments_fetched}")
                for reply in replies:
                    sleep(delay() + 1)
                    text, styled_text = await parse_comment_text(reply)
                    styled_text = style_reply_mention(styled_text)
                    like_count, channel_username, comment_date, channel_url, channel_pfp = parse_comments(reply)
                    heart = reply.css_first('#creator-heart-button')
                    if heart:
                        heart = youtube_html_elements.heart(profile_image)
                    else:
                        heart = ""
                    reply_box = youtube_html_elements.reply_box(
                        channel_url, channel_pfp, channel_username, comment_date, styled_text, like_count, heart
                    )
                    output.write(reply_box)
                    author_heart = bool(heart)
                    reply_dict = {
                        "text": text,
                        "like_count": like_count,
                        "channel_username": channel_username,
                        "comment_date": comment_date,
                        "channel_url": channel_url,
                        "channel_pfp": channel_pfp,
                        "author_heart": author_heart
                    }
                    comment_dict["replies"].append(reply_dict)
            comments_list.append(comment_dict)
        print(f"[DEBUG] Saving {len(comments_list)} comments to JSON file...")
        save_comments_to_json_file(f"{output_directory}/comments.json", comments_list)
    except Exception as e:
        logging.error(f"Error while fetching comments: {e}\n{traceback.format_exc()}")
        print(f"[ERROR] Exception occurred: {e}\n{traceback.format_exc()}")