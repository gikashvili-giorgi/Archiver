# Archiver

Save YouTube videos offline, complete with metadata, in an HTML interface that replicates the YouTube experience.

[Download an example output](https://drive.google.com/file/d/1GhoVJkxn6OMTzPKwNgKyUam3NgUeVo0b/view?usp=sharing)

![archiver_thumbnail](https://i.imgur.com/0KuTe24.png)

---

## Features
- Download YouTube videos and metadata for offline access
- Generates a YouTube-like HTML interface for easy browsing
- Saves comments, channel info, and video details
- Preserves video thumbnails and assets
- OSINT-friendly: visualize and archive online content

---

## Use Cases
- Create a personal offline library of your favorite YouTube content
- Archive videos that may be deleted or geo-blocked
- Digital preservation for research, OSINT, or personal use
- Access videos in regions with restricted internet

---

## How it Works
Archiver uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) for downloading and [nodriver](https://github.com/ultrafunkamsterdam/nodriver) for browser automation. The workflow:

1. **Download Videos:** Uses yt-dlp to fetch videos and metadata
2. **Collect Metadata:** Gathers video info, comments, and channel details
3. **Generate HTML:** Compiles everything into a browsable HTML file with assets

---

## Prerequisites
- Python 3.11+
- Latest version of Google Chrome (required for nodriver)

---

## Setup
1. **Clone the repository:**
   ```sh
   git clone https://github.com/gikashvili-giorgi/Archiver.git
   cd Archiver
   ```
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
   *On Windows, you can run `requirements.cmd` instead.*
3. **Ensure Google Chrome is up to date.**
4. **Configure settings:**
   - Edit `settings.json` to customize options (see below).

---

## Settings
Edit `settings.json` to control Archiver's behavior:

- `youtube > save_comments`: `true` or `false` — Save YouTube comments
- `youtube > max_comments`: Maximum number of comments to save (e.g., `1000`)
- `extra > delay`: Delay (in seconds) between actions (default: `1`)
- `extra > headless`: Run Chrome in headless mode (`true`/`false`)
- `extra > split_tabs`: Use separate tabs for each video (`true`/`false`)
- `extra > profile`: Chrome profile to use (default: `Default`)

**Note:**
- The `headless` option may not work reliably on all systems.
- If `headless` is `false`, keep the Chrome window open and avoid minimizing it. For multitasking, resize the window instead of minimizing.

---

## Usage
To start Archiver, run:

```sh
python3 archiver.py
```

*On Windows, you can use the `start.cmd` script for easy launch.*

- The HTML output is saved in the `youtube_downloads` folder.
- If you move the HTML file, also copy the `styles` folder and `assets` directory for full functionality.

---

## Development
- **Format code:**
  ```sh
  black .
  ```
- **Run tests:**
  ```sh
  pytest
  ```
- **Install dev dependencies:**
  ```sh
  pip install -r requirements-dev.txt
  ```

---

## Troubleshooting
- Ensure Chrome is up to date if you encounter browser errors.
- Check `settings.json` for typos or invalid values.
- For issues with dependencies, try reinstalling with `pip install -r requirements.txt`.

---

## To-Do List
- [ ] Add support for Instagram and TikTok downloads

---

## Credits
- Huge thanks to [@virag-ky](https://github.com/virag-ky/Youtube-Clone) for the HTML/CSS template inspiration
- For help, contact @`gikashvili` on Discord
