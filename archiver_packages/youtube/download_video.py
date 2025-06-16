import yt_dlp
from archiver_packages.utilities.utilities import clear
from rich.console import Console
from rich.table import Table


def fetch_videos_info(video_url: str) -> dict:
    """Fetch metadata for a list of YouTube videos."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'forcetitle': True,
        'writesubtitles': False,
        'writeautomaticsub': False,
        'writeinfojson': False,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url)
        return info

def input_youtube_links(download_playlist: bool) -> list[str]:
    """Prompt user for YouTube links and display info table."""
    console = Console()
    yt_links = []
    info_list = []
    try:
        while True:
            console.print("[bold yellow]\nNOTE:[/bold yellow]")
            console.print("Add YouTube Video/Playlist/Channel URLs one by one. Finally type 'S/s' to start", style="cyan")
            link = input("\n >> Add YouTube link: ")
            if link.lower() == 's':
                break
            if link not in yt_links:
                if download_playlist is False:
                    link = link.split("&")[0]
                    yt_links.append(link)
                else:
                    yt_links.append(link)
            clear()
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Author", style="dim")
            table.add_column("Title")
            table.add_column("Link", overflow="fold")
            info = fetch_videos_info(yt_links[-1])
            info_list.append(info)
            for yt_link, info in zip(yt_links, info_list):
                video_title = info.get('title', None)
                channel_author = info.get('uploader', None)
                table.add_row(str(channel_author), str(video_title), yt_link)
            console.print(table)
    except Exception:
        console.print("[bold red]Make sure, the YouTube links are in a correct format.[/bold red]")
    return yt_links

def get_youtube_links_from_playlist_and_channel(playlist_link: str) -> list[str]:
    """Extract all video links from a playlist or channel."""
    with yt_dlp.YoutubeDL() as ydl:
        playlist_dict = ydl.extract_info(playlist_link, download=False)
        video_list = playlist_dict.get('entries', [])
        youtube_links = [video['webpage_url'] for video in video_list]
        return youtube_links

def download_videos_with_info(video_urls: list, output_directory: str, skip_download: bool = False) -> list[dict]:
    """Download YouTube videos and return their metadata."""
    ydl_opts = {
        'quiet': True,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
        'no_warnings': True,
        'forcetitle': True,
        'writesubtitles': False,
        'writeautomaticsub': False,
        'writeinfojson': True,
        'writecomments': True,
        'skip_download': skip_download,
        'merge_output_format': 'mp4',
        'outtmpl': f"{output_directory}/%(title)s [%(id)s].%(ext)s"
    }
    info_list = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for video_url in video_urls:
            info = ydl.extract_info(video_url)
            info_list.append(info)
    return info_list

def download_best_audio(url: str, output_directory: str) -> None:
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f"{output_directory}/%(title)s [%(id)s].%(ext)s",
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])