from typing import List

MAX_TITLE_LENGTH = 20


def truncate_title(title: str, max_length: int = MAX_TITLE_LENGTH) -> str:
    text = (title or "").strip()
    if not text:
        return ""
    return text[:max_length]


def truncate_titles(titles: List[str], max_length: int = MAX_TITLE_LENGTH) -> List[str]:
    if not isinstance(titles, list):
        return []
    result: List[str] = []
    for item in titles:
        title = truncate_title(str(item or ""), max_length=max_length)
        if title:
            result.append(title)
    return result
