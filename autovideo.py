from __future__ import annotations

import argparse
import html
import re
import subprocess
import textwrap
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import List
from urllib.request import Request, urlopen


@dataclass
class Article:
    title: str
    paragraphs: List[str]


class _ArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_title = False
        self._in_paragraph = False
        self._title_parts: List[str] = []
        self._paragraph_parts: List[str] = []
        self.paragraphs: List[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag == "title":
            self._in_title = True
        elif tag == "p":
            self._in_paragraph = True
            self._paragraph_parts = []

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag == "title":
            self._in_title = False
        elif tag == "p" and self._in_paragraph:
            self._in_paragraph = False
            paragraph = _normalize("".join(self._paragraph_parts))
            if paragraph:
                self.paragraphs.append(paragraph)

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        if self._in_title:
            self._title_parts.append(data)
        elif self._in_paragraph:
            self._paragraph_parts.append(data)

    @property
    def title(self) -> str:
        return _normalize("".join(self._title_parts))


def _normalize(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fetch_html(url: str, timeout: int = 15) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; autovideo/1.0; +https://github.com/hiepnh123/autovideo)"
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="ignore")


def extract_article_content(raw_html: str) -> Article:
    parser = _ArticleParser()
    parser.feed(raw_html)

    title = parser.title or "Tin tức"
    paragraphs = parser.paragraphs

    if not paragraphs:
        text = _normalize(re.sub(r"<[^>]+>", " ", raw_html))
        if text:
            paragraphs = [text]

    return Article(title=title, paragraphs=paragraphs)


def summarize_article(article: Article, max_sentences: int = 6) -> str:
    body = " ".join(article.paragraphs)
    sentences = re.split(r"(?<=[.!?])\s+", body)
    selected = [s.strip() for s in sentences if s.strip()][:max_sentences]
    summary = " ".join(selected)
    return summary or article.title


def _escape_for_drawtext(text: str) -> str:
    escaped = text.replace("\\", r"\\")
    escaped = escaped.replace(":", r"\:")
    escaped = escaped.replace("'", r"\'")
    escaped = escaped.replace("%", r"\%")
    return escaped


def _wrap_text(text: str, width: int = 38) -> str:
    wrapped = textwrap.fill(text, width=width)
    return wrapped.replace("\n", r"\n")


def build_video_command(
    article: Article,
    summary: str,
    output_path: Path,
    duration: int = 20,
    ffmpeg_bin: str = "ffmpeg",
) -> List[str]:
    title_text = _escape_for_drawtext(_wrap_text(article.title, width=32))
    body_text = _escape_for_drawtext(_wrap_text(summary, width=44))

    draw_title = (
        "drawtext=fontcolor=white:fontsize=52:line_spacing=10:"
        "x=(w-text_w)/2:y=80:text='"
        + title_text
        + "'"
    )
    draw_body = (
        "drawtext=fontcolor=white:fontsize=34:line_spacing=8:"
        "x=(w-text_w)/2:y=220:text='"
        + body_text
        + "'"
    )

    filter_chain = f"{draw_title},{draw_body}"

    return [
        ffmpeg_bin,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=0x0f172a:s=1280x720:d={duration}",
        "-vf",
        filter_chain,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output_path),
    ]


def create_video_from_news_url(
    url: str,
    output_path: Path,
    duration: int = 20,
    ffmpeg_bin: str = "ffmpeg",
    dry_run: bool = False,
) -> List[str]:
    raw_html = fetch_html(url)
    article = extract_article_content(raw_html)
    summary = summarize_article(article)
    command = build_video_command(
        article=article,
        summary=summary,
        output_path=output_path,
        duration=duration,
        ffmpeg_bin=ffmpeg_bin,
    )

    if not dry_run:
        subprocess.run(command, check=True)

    return command


def main() -> None:
    cli = argparse.ArgumentParser(description="Tạo video từ URL tin tức")
    cli.add_argument("url", help="URL bài báo")
    cli.add_argument("--output", default="news-video.mp4", help="File video đầu ra")
    cli.add_argument("--duration", type=int, default=20, help="Thời lượng video (giây)")
    cli.add_argument(
        "--dry-run",
        action="store_true",
        help="Chỉ in lệnh ffmpeg sẽ chạy, không render video",
    )
    args = cli.parse_args()

    command = create_video_from_news_url(
        url=args.url,
        output_path=Path(args.output),
        duration=max(args.duration, 1),
        dry_run=args.dry_run,
    )

    if args.dry_run:
        print(" ".join(command))


if __name__ == "__main__":
    main()
