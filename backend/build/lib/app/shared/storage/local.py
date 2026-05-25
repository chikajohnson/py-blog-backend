from pathlib import Path
from app.shared.storage.base import StorageProvider


class LocalFileStorage(StorageProvider):
    def __init__(self, base_dir: str = "./uploads", base_url: str = "/uploads"):
        self.base_dir = Path(base_dir)
        self.base_url = base_url.rstrip("/")

    async def save(self, file_data: bytes, path: str) -> str:
        full_path = self.base_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(file_data)
        return f"{self.base_url}/{path}"

    async def delete(self, path: str) -> bool:
        full_path = self.base_dir / path
        if full_path.exists():
            full_path.unlink()
            return True
        return False

    async def exists(self, path: str) -> bool:
        return (self.base_dir / path).exists()
