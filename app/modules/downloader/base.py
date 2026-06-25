from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class DownloadResult:
    source: str
    url: str
    title: str
    file_path: Path
    content_type: str
    duration_seconds: Optional[float] = None
    size_bytes: Optional[int] = None


class BaseDownloader(ABC):
    source_key: str
    label: str
    enabled: bool = True

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def download(self, url: str, output_dir: Path) -> DownloadResult:
        raise NotImplementedError
