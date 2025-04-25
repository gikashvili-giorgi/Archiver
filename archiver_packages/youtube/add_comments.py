import logging
from selectolax.parser import HTMLParser
from bs4 import BeautifulSoup
from time import sleep
import json
from archiver_packages.utilities.nodriver_utils import slow_croll, page_scroll, scroll_until_elements_loaded, activate_dialog_window
from archiver_packages.youtube.extract_comment_emoji import convert_youtube_emoji_url_to_emoji
import archiver_packages.youtube_html_elements as youtube_html_elements
from typing import Callable
import urllib.parse

logging.basicConfig(level=logging.INFO)

def format_text_emoji(input_text:str) -> str:
    """
    Format text with emojis.
    """
    lines = input_text.split('\n')
    merged_lines = []

    for i in range(len(lines)):
        if i > 0 and len(lines[i]) == 1:
            merged_lines[-1] += ' ' + lines[i]
        else:
            merged_lines.append(lines[i])

    return '\n'.join(merged_lines)


async def parse_comment_text(comment_ele) -> tuple[str]:
    """
    Parse comments/replies text.
    """

    text_ele = await comment_ele.query_selector('#content-text')
    text_ele_html = await text_ele.get_html()

    soup = BeautifulSoup(text_ele_html, 'html.parser')

    # Replace <img> tags with emoji
    for img_ele in soup.find_all(lambda tag: tag.name=="img" and tag.has_attr('src') and "emoji" in tag["src"]):
        emoji_url = img_ele["src"]
        emoji = convert_youtube_emoji_url_to_emoji(emoji_url)
        img_ele.replace_with(emoji)

    url_list, timestamp_list = [], []

    # Replace url tags with url
    for url_ele in soup.find_all(lambda tag: tag.name=="a" and tag.has_attr('href') and "https://" in tag.text):
        url = url_ele.text.strip()
        url_ele.replace_with(url)
        url_list.append(url)

    # Replace timestamp <a> tags with styled timestamp  
    for url_ele in soup.find_all(lambda tag: tag.name=="a" and tag.has_attr('href') and "&t=" in tag["href"]):
        timestamp_url = url_ele["href"]
        timestamp_url = "https://www.youtube.com/" + timestamp_url
        timestamp_text = url_ele.text.strip()
        url_ele.replace_with(timestamp_text)
        timestamp_list.append({"text":timestamp_text,"url":timestamp_url})

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
        styled_timestamp = youtube_html_elements.redirect_url(timestamp_text,timestamp_url)

        styled_text = styled_text.replace(timestamp_text, styled_timestamp)

    return text, styled_text


def style_reply_mention(input_text:str) -> str:
    """
    Style reply mentions.
    """
    input_text = input_text.strip()

    if input_text.startswith('@'):

        # Extract the first word
        words = input_text.split(' ', 1)

        if len(words) > 1: # Check if there is more than one word to ensure that we have an actual mention instead of a one-word reply that starts with the '@' symbol
            mention, remaining_text = words
            mention = mention.strip()

            # Apply style to the mention
            input_text = youtube_html_elements.mention(mention)
            input_text = f"{input_text} {remaining_text}"

    return input_text


def parse_comments(html:HTMLParser) -> tuple[str, str, str, str, str]:
    """
    Parse comments.
    """
    like_count = html.css_first("[id='vote-count-middle']").text().strip()

    channel_username = html.css_first("[id='author-text']").attributes.get("href")[1:]

    comment_date = html.css_first("div[id='header-author'] span[id='published-time-text'] a").text().strip()

    channel_url = html.css_first("div[id='main'] div a").attributes.get("href")
    channel_url = "https://www.youtube.com" + channel_url

    channel_pfp = html.css_first("yt-img-shadow [id='img']").attributes.get("src")
    channel_pfp = channel_pfp.replace("s88-c-k", "s48-c-k")

    return (like_count,channel_username,comment_date,channel_url,channel_pfp)


async def load_all_comments(tab,delay:Callable[[int],float],max_comments:int,comment_count:int):
    """ Scroll to end of the page to load all comments. """

    # Click on button to activate End key scroll
    sleep(delay()+2)
    activate_btn = await tab.select("#owner-sub-count")
    await activate_dialog_window(activate_btn,delay)
    sleep(delay()+2)

    # Scroll to the bottom of the page to load all comments
    await scroll_until_elements_loaded(
        tab=tab,
        number_of_elements=comment_count,
        number_of_page_results=20,
        delay=delay,
        extra_scrolls=5,
        )

    # Scroll to the bottom of the page
    page_end_count = 0
    while True:
        if await page_scroll(tab,delay) == "page_end":
            page_end_count += 1
            if page_end_count > 3:
                break
            if page_end_count > 2:
                sleep(delay()+1)
                await slow_croll(tab,delay) # Scroll to description section and wait for comments to load
        else:
            page_end_count = 0

        comments = await tab.select_all('#contents ytd-comment-thread-renderer')
        comments_count = len(comments)

        if comments_count > max_comments:
            break

    return comments


async def check_for_pinned_comment(comment,comments_fetched:int) -> bool:
    """
    Check if the comment is pinned.
    """
    is_comment_pinned = False

    if comments_fetched == 1:
        pinned_comment_elements = await comment.query_selector_all("ytd-pinned-comment-badge-renderer")

        if len(pinned_comment_elements) > 0:
            is_comment_pinned = True

    return is_comment_pinned


def save_comments_to_json_file(path:str,comments_list:list[dict]):
    """
    Save comments to a JSON file.
    """
    if comments_list != []:
        data = json.dumps(comments_list, indent=4)

        with open(path, "w") as outfile:
            outfile.write(data)


async def add_comments(tab,output_directory:str,profile_image:str,comment_count:int,channel_author:str,output,delay:Callable[[int],float],max_comments:int):
    """
    Fetch and process YouTube comments, saving them to HTML and JSON.
    """
    await slow_croll(tab,delay) # Scroll to description section and wait for comments to load

    logging.info("Loading comments...")
    comments = await load_all_comments(tab,delay,max_comments,comment_count)
    comments = comments[:max_comments]

    logging.info("Fetching comments...")
    comments_count = len(comments)
    comments_fetched = 0
    comments_list = []

    try:
        for comment in comments:
            comments_fetched += 1
            logging.info(f"Fetched {comments_fetched}/{comments_count} comments.", end='\r')

            # Check for pinned comment
            is_comment_pinned = await check_for_pinned_comment(comment,comments_fetched)

            # Scroll to comment
            await comment.scroll_into_view()
            sleep(delay()+1)

            text, styled_text = await parse_comment_text(comment)

            # comment_inner_html = await comment.evaluate("(element) => element.innerHTML")
            comment_html = await comment.get_html()

            html_comment = HTMLParser(comment_html)
            like_count,channel_username,comment_date,channel_url,channel_pfp = parse_comments(html_comment)

            # Add heart icon if present
            heart = html_comment.css_first('#creator-heart-button')
            if heart:
                heart = youtube_html_elements.heart(profile_image)
            else:
                heart = ""

            comment_box = youtube_html_elements.comment_box(channel_url,channel_pfp,channel_username,channel_author,comment_date,styled_text,like_count,heart,is_comment_pinned)
            divs = youtube_html_elements.ending.divs

            # Save comment metadata to dict
            author_heart = True if heart else False
            comment_dict = {
                "text": text,
                "like_count":like_count,
                "channel_username":channel_username,
                "comment_date":comment_date,
                "channel_url":channel_url,
                "channel_pfp":channel_pfp,
                "author_heart":author_heart,
                "replies": []
            }

            replies_btn = await comment.query_selector_all("#more-replies button")

            if len(replies_btn) == 0:
                # Add comment HTML
                comment_box += divs
                output.write(comment_box)

            else:
                # Add blue reply toggle
                reply_count = html_comment.css_first("[id='more-replies'] button")

                try:
                    reply_count = reply_count.attributes.get("aria-label")
                except:
                    reply_count = reply_count.text()

                replies_toggle = youtube_html_elements.replies_toggle(reply_count)

                # Add comment HTML
                comment_box += replies_toggle + divs
                output.write(comment_box)

                # Click replies button to load replies
                sleep(delay())
                replies_btn = await comment.query_selector("#more-replies button")
                await replies_btn.click()
                sleep(delay()+2)
                await slow_croll(tab, delay)
                sleep(delay()+5)

                # Click Show more replies button
                while True:
                    show_more_replies = await comment.query_selector_all("button[aria-label='Show more replies']")

                    if len(show_more_replies) > 0:
                        show_more_replies_btn = show_more_replies[0]
                        await show_more_replies_btn.scroll_into_view()
                        sleep(delay()+1)
                        await show_more_replies_btn.click()
                        sleep(delay()+2)
                        await slow_croll(tab, delay)
                        sleep(delay()+5)
                    else:
                        break

                replies = await comment.query_selector_all('div[id="expander"] div[id="expander-contents"] #body')

                for reply in replies:

                    await reply.scroll_into_view() # Slow scroll replies
                    sleep(delay()+1)

                    text, styled_text = await parse_comment_text(reply)
                    styled_text = style_reply_mention(styled_text)

                    reply_html = await reply.get_html()

                    html_reply = HTMLParser(reply_html)
                    like_count,channel_username,comment_date,channel_url,channel_pfp = parse_comments(html_reply)

                    # Add heart icon if present
                    heart = html_reply.css_first('#creator-heart-button')
                    if heart:
                        heart = youtube_html_elements.heart(profile_image)
                    else:
                        heart = ""

                    # Add reply
                    reply_box = youtube_html_elements.reply_box(channel_url,channel_pfp,channel_username,comment_date,styled_text,like_count,heart)
                    output.write(reply_box)

                    # Save reply metadata to comment dict
                    author_heart = True if heart else False
                    reply_dict = {
                        "text": text,
                        "like_count":like_count,
                        "channel_username":channel_username,
                        "comment_date":comment_date,
                        "channel_url":channel_url,
                        "channel_pfp":channel_pfp,
                        "author_heart":author_heart
                    }
                    comment_dict["replies"].append(reply_dict)

            comments_list.append(comment_dict)

        save_comments_to_json_file(f"{output_directory}/comments.json",comments_list)

    except Exception as e:
        logging.error(f"No Such Element...{e}")
        pass