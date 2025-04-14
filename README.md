# Archiver    
Save YouTube videos offline, complete with metadata, in an HTML interface that replicates the YouTube experience.
Download an [example output](https://f92.workupload.com/download/v4EBZxM5qUT)

![archiver_thumbnail](https://i.imgur.com/0KuTe24.png)

## Use Cases
- Create a personal offline library of your favorite YouTube content.
- Download YouTube videos that may be deleted later.
- Archiver can also be used as an OSINT tool to better visualize gathered information.
- Ensure access to videos in regions with restricted internet access.
- Use it as a tool for digital archiving and preservation of online media.

## How it Works
Archiver relies on the Selenium and yt-dlp modules to function effectively. Here's a breakdown of its process:

1. Downloading YouTube Videos: Archiver initiates by downloading YouTube videos locally using yt-dlp.
2. Collecting Metadata: Alongside the video downloads, Archiver gathers essential metadata associated with each YouTube video.
3. Compilation into HTML Format: After completing the downloads and metadata collection, Archiver assembles the YouTube videos and their corresponding metadata into an HTML file for easy access and reference.

## Prerequisites
1. Python 3.10+
2. Latest version of Google Chrome

## Setup
1. Download the code directly or clone the repository using `git clone https://github.com/ZG4RBU/Archiver.git`.
2. Install the necessary modules listed in `requirements.txt` by running `pip install -r requirements.txt`. Alternatively, on Windows, you can simply run the `requirements.cmd` script.
3. Make sure you have the latest version of Google Chrome installed. This is required for the Selenium ChromeDriver component.
4. Customize the `settings.json` file according to your preferences.

## Settings
`youtube > save_comments` > Enter true/false.

`extra > delay` > Delay per action.

`extra > headless` > Run chrome as background process. Enter true/false.

NOTE:
When setting the headless option to false, it's essential to keep the Chrome browser window open and avoid minimizing it. If you need to multitask, it's recommended to resize the browser window to one half of the screen for a seamless working experience.


## Usage
To start the code, execute the following command:
```
python3 archiver.py
```
If you're on Windows, you can use the `start.cmd` script for an easy launch.
- The HTML output is saved in the `youtube_downloads` folder.
- When moving the HTML file outside the folder, make sure to also copy the `css` file and `assets` folder.

## To-Do List
- [ ] Implement support for downloading content from Instagram and TikTok

## Credits
big thanks to @virag-ky for [this](https://github.com/virag-ky/Youtube-Clone) awesome html/css  

For help contact @`gikashvili` (Discord)
