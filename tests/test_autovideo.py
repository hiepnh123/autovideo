import unittest
from pathlib import Path
from unittest.mock import patch

from autovideo import (
    Article,
    build_video_command,
    create_video_from_news_url,
    extract_article_content,
    summarize_article,
)


class AutoVideoTests(unittest.TestCase):
    def test_extract_article_content(self):
        raw_html = """
        <html>
            <head><title>Bản tin sáng nay</title></head>
            <body>
                <p>Thị trường chứng khoán tăng nhẹ.</p>
                <p>Nhà đầu tư kỳ vọng lãi suất giảm.</p>
            </body>
        </html>
        """

        article = extract_article_content(raw_html)

        self.assertEqual(article.title, "Bản tin sáng nay")
        self.assertEqual(
            article.paragraphs,
            [
                "Thị trường chứng khoán tăng nhẹ.",
                "Nhà đầu tư kỳ vọng lãi suất giảm.",
            ],
        )

    def test_build_video_command(self):
        article = Article(
            title="Bản tin kinh tế",
            paragraphs=["Nền kinh tế phục hồi ổn định.", "Lạm phát được kiểm soát."],
        )
        summary = summarize_article(article)

        command = build_video_command(
            article=article,
            summary=summary,
            output_path=Path("out.mp4"),
            duration=25,
            ffmpeg_bin="ffmpeg",
        )

        self.assertEqual(command[0], "ffmpeg")
        self.assertIn("color=c=0x0f172a:s=1280x720:d=25", command)
        self.assertEqual(command[-1], "out.mp4")

    @patch("autovideo.fetch_html")
    @patch("autovideo.subprocess.run")
    def test_create_video_from_news_url_dry_run(self, mock_run, mock_fetch):
        mock_fetch.return_value = """
        <html><head><title>Tin công nghệ</title></head>
        <body><p>Sản phẩm mới ra mắt hôm nay.</p></body></html>
        """

        command = create_video_from_news_url(
            url="https://example.com/news",
            output_path=Path("news.mp4"),
            duration=15,
            dry_run=True,
        )

        mock_run.assert_not_called()
        self.assertEqual(command[0], "ffmpeg")
        self.assertEqual(command[-1], "news.mp4")


if __name__ == "__main__":
    unittest.main()
