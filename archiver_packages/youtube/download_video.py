import yt_dlp
from archiver_packages.utilities.utilities import clear



def fetch_videos_info(video_urls:list) -> list[dict]:
    ydl_opts = {
        'quiet': True,  # No stdout output
        'no_warnings': True,
        'forcetitle': True,
        'writesubtitles': False,
        'writeautomaticsub': False,
        'writeinfojson': False,
        'skip_download': True,
    }

    info_list = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for video_url in video_urls:
            info = ydl.extract_info(video_url)
            info_list.append(info)

    return info_list


def input_youtube_links() -> list[str]:

    yt_links = []
    try:
        while True:
            print("\nNOTE:")
            print("Add YouTube Video/Playlist/Channel URLs one by one. Finally type 'S/s' to start")
            link = input("\n >> Add YouTube link: ")

            if link.lower()=='s':
                break
            if link not in yt_links: # Avoid duplicates
                yt_links.append(link)

            # Print Full list
            clear()
            print("Author\t Title\t  Link\t")

            info_list = fetch_videos_info(yt_links)

            for yt_link,info in zip(yt_links,info_list):
                video_title = info.get('title', None)
                channel_author = info.get('uploader', None)

                print(channel_author + '\t '+ video_title + '\t ' + yt_link)
    except:
        print(f"Make sure, the YouTube links are in a correct format.")

    return yt_links


def get_youtube_links_from_playlist_and_channel(playlist_link:str) -> list[str]:

    with yt_dlp.YoutubeDL() as ydl:
        playlist_dict = ydl.extract_info(playlist_link, download=False)
        video_list = playlist_dict.get('entries', [])

        youtube_links = []

        for video in video_list:
            youtube_links.append(video['webpage_url'])

        return youtube_links


def download_videos_with_info(video_urls:list,output_directory:str,skip_download:bool=False) -> list[dict]:

    ydl_opts = {
        'quiet': True,  # No stdout output
        'format': 'bestvideo+bestaudio/best',
        'no_warnings': True,
        'forcetitle': True,
        'writesubtitles': False,
        'writeautomaticsub': False,
        'writeinfojson': True,
        'writecomments': True,  # Enables downloading comments
        'skip_download': skip_download,
        'merge_output_format': 'mp4',  # Ensures the final output is in mp4 format
        'outtmpl': f"{output_directory}/%(title)s [%(id)s].%(ext)s"
    }

    info_list = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for video_url in video_urls:
            info = ydl.extract_info(video_url, download=True)
            info_list.append(info)

    return info_list