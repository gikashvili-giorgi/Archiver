@echo off

:start
cls

pip install --upgrade psutil
pip install --upgrade requests
pip install --upgrade nodriver
pip install --upgrade "yt-dlp[default]>=2026.8.19"
pip install --upgrade beautifulsoup4
pip install --upgrade youtube-comment-downloader

pause
exit
