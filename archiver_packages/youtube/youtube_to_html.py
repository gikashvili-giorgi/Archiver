import os, re
from archiver_packages.youtube.extract_info import scrape_info, download_youtube_thumbnail
from archiver_packages.youtube.add_comments import add_comments
from archiver_packages.utilities.utilities import convert_date_format
from archiver_packages.utilities.file_utils import copy_file_or_directory
from typing import Callable
import archiver_packages.youtube_html_elements as youtube_html_elements



def modify_exctracted_info(yt_url:str,video_publish_date:str,channel_keywords:list,channel_description:str,like_count:int|None,dislike_count:int|None,comment_count:int|None) -> tuple:

    # Remove timecode from video URL
    if "&" in yt_url:
        yt_url = yt_url.split("&")[0]

    # Modify date format
    video_publish_date = convert_date_format(video_publish_date)

    # Add hashtag to keyword tags
    channel_keywords = ['#'+i for i in channel_keywords]
    channel_keywords = ' '.join(channel_keywords)

    # Make description link-clickable
    channel_description = re.sub(r'http\S+', '<a href="' + "\\g<0>" + '">' + "\\g<0>" + '</a>', channel_description) ###

    # Make hashtags clickable
    description_hashtags = re.findall(r"#\w+", channel_description)
    for description_hashtag in description_hashtags:
        hashtag_url = "https://www.youtube.com/hashtag/" + description_hashtag.lower()[1:]
        hashtag = youtube_html_elements.redirect_url(description_hashtag,hashtag_url)
        channel_description = channel_description.replace(description_hashtag, hashtag)

    # Make description timestamp clickable
    description_timestamps = re.findall(r'(?<!\d)(\d+:\d{2})\b', channel_description)
    for description_timestamp in description_timestamps:

        # Convert to seconds
        minutes, seconds = map(int, description_timestamp.split(':'))
        description_timestamp_in_seconds = minutes * 60 + seconds

        timestamp_url = yt_url + f"&t={description_timestamp_in_seconds}s"
        timestamp = youtube_html_elements.redirect_url(description_timestamp,timestamp_url)
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
    if comment_count is not None:
        comment_count = f"{comment_count:,} Comments"
    else:
        comment_count = "Comments are turned off."

    return (yt_url,video_publish_date,channel_keywords,channel_description,like_count,dislike_count,comment_count)


def get_html_output_dir(video_id:str,root_directory:str) -> str:

    for dir in os.listdir(root_directory):
        if video_id in dir:
            return dir


async def parse_to_html(output_directory:str,yt_urls:list[str],files:list[str],info_list:list[dict],driver,delay:Callable[[int],float],save_comments:bool,max_comments:int,split_tabs:bool):

    for (yt_url,file,info) in zip(yt_urls,files,info_list):

        filename = os.path.basename(file)

        # Extract the relevant pieces of information
        video_title = info.get('title', None)
        video_views = info.get('view_count', None)
        channel_author = info.get('uploader', None)
        channel_url = info.get('uploader_url', "Channel URL not found")
        video_publish_date = info.get('upload_date', None)
        channel_keywords = info.get('tags', None)
        channel_description = info.get('description', None)
        subscribers = info.get('channel_follower_count', None)
        like_count = info.get('like_count', None)
        dislike_count = info.get('dislike_count', None)
        comment_count:int|None = info.get('comment_count', None)
        video_id = info.get("id")

        yt_url,video_publish_date,channel_keywords,channel_description,like_count,dislike_count,comment_count_str = modify_exctracted_info(yt_url,video_publish_date,channel_keywords,channel_description,like_count,dislike_count,comment_count)

        # html_output_dir = get_html_output_dir(video_id,output_directory)

        # Download thumbnail
        download_youtube_thumbnail(info,f"{output_directory}/{video_id}_thumbnail.jpg")

        input = open("./archiver_packages/youtube_html/index.html", 'rt', encoding="utf8")
        output = open(f"{output_directory}/YouTube.html", 'wt', encoding="utf8")

        # Scrape additional info
        tab, profile_image = await scrape_info(driver,yt_url,delay,split_tabs)

        for line in input:
            output.write(
                line.replace('REPLACE_TITLE', video_title)
                .replace('TITLE_URL', yt_url)
                .replace('NUMBER_OF_VIEWS', f'{video_views:,}')
                .replace('CHANNEL_AUTHOR', channel_author)
                .replace('CHANNEL_URL', channel_url)
                .replace('PUBLISH_DATE', f'{video_publish_date}')
                .replace('CHANNEL_KEYWORDS', f'{channel_keywords}')
                .replace('CHANNEL_DESCRIPTION', channel_description)
                .replace('CHANNEL_SUBSCRIBERS', f'{subscribers:,} subscribers')
                .replace('PROFILE_IMAGE_LINK', profile_image)
                .replace('LIKE_COUNT', like_count)
                .replace('DISLIKES_COUNT', dislike_count)
                .replace('COMMENT_COUNT', f'{comment_count_str}')
                .replace('VIDEO_SOURCE', f'{filename}')
            )

        if save_comments == True:
            await add_comments(tab,output_directory,profile_image,comment_count,channel_author,output,delay,max_comments)

        output.write(youtube_html_elements.ending.html_end)
        print(f"HTML file created for {video_title}")

        input.close()
        output.close()

        # Copy assets and styles folders to html output dir
        folders = ["assets","styles"]

        for folder in folders:
            copy_file_or_directory(
                f"archiver_packages/youtube_html/{folder}",
                output_directory
            )