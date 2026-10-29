# autovideo

Tạo video từ URL tin tức bằng một lệnh Python đơn giản.

## Cách dùng

```bash
python /home/runner/work/autovideo/autovideo/autovideo.py "https://example.com/news" --output news.mp4
```

### Chạy thử không render video

```bash
python /home/runner/work/autovideo/autovideo/autovideo.py "https://example.com/news" --dry-run
```

Tham số:
- `--output`: đường dẫn file video đầu ra (mặc định `news-video.mp4`)
- `--duration`: thời lượng video theo giây (mặc định `20`)
- `--dry-run`: chỉ in lệnh `ffmpeg` sẽ chạy
