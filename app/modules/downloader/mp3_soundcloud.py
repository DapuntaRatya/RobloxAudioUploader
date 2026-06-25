from app.modules.downloader.mp3_youtube import YouTubeMp3Downloader


class SoundCloudMp3Downloader(YouTubeMp3Downloader):
    source_key = "soundcloud"
    label = "SoundCloud"
    enabled = True

    def can_handle(self, url: str) -> bool:
        return "soundcloud.com" in url.lower()
