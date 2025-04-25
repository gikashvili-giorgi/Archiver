import re

def extract_emoji_unicode(url: str) -> str | None:
    pattern = r"emoji_(\w+)\.png"
    matches = re.findall(pattern, url)
    return matches[0] if matches else None

def convert_to_unicode(emoji_unicode: str) -> str:
    emoji_unicode = emoji_unicode.strip('u').upper().zfill(8)
    return '\\U' + emoji_unicode

def unicode_to_emoji(text: str) -> str:
    unicode_pattern = re.compile(r'\\U[0-9a-fA-F]{8}')
    def replace(match):
        char = match.group(0)
        return chr(int(char[2:], 16))
    return unicode_pattern.sub(replace, text)

def convert_youtube_emoji_url_to_emoji(url: str) -> str:
    if not url:
        return ""
    url_unicode = extract_emoji_unicode(url)
    if url_unicode:
        unicode_code = convert_to_unicode(url_unicode)
        return unicode_to_emoji(unicode_code)
    return ""

if __name__ == '__main__':
    url = "https://www.youtube.com/s/gaming/emoji/7ff574f2/emoji_u1f525.png"
    print(convert_youtube_emoji_url_to_emoji(url))