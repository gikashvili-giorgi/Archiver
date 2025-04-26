import re


def extract_emoji_unicode(url: str) -> str | None:
    """Extract emoji unicode from a YouTube emoji URL."""
    pattern = r"emoji_(\w+)\.png"
    matches = re.findall(pattern, url)
    return matches[0] if matches else None


def convert_to_unicode(emoji_unicode: str) -> str:
    """Convert emoji unicode string to Python unicode escape."""
    emoji_unicode = emoji_unicode.strip('u').upper().zfill(8)
    return f'\\U{emoji_unicode}'


def unicode_to_emoji(text: str) -> str:
    """Convert unicode escape string to emoji character."""
    unicode_pattern = re.compile(r'\\U[0-9a-fA-F]{8}')
    def replace(match):
        char = match.group(0)
        return chr(int(char[2:], 16))
    return unicode_pattern.sub(replace, text)


def convert_youtube_emoji_url_to_emoji(url: str) -> str:
    """Convert a YouTube emoji URL to the actual emoji character."""
    if not url:
        return ""
    url_unicode = extract_emoji_unicode(url)
    if url_unicode:
        unicode_code = convert_to_unicode(url_unicode)
        return unicode_to_emoji(unicode_code)
    return ""


def main():
    url = "https://www.youtube.com/s/gaming/emoji/7ff574f2/emoji_u1f525.png"
    print(convert_youtube_emoji_url_to_emoji(url))


if __name__ == '__main__':
    main()