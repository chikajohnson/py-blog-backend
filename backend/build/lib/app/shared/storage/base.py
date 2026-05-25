from abc import ABC, abstractmethod


class StorageProvider(ABC):
    @abstractmethod
    async def save(self, file_data: bytes, path: str) -> str: ...
    @abstractmethod
    async def delete(self, path: str) -> bool: ...
    @abstractmethod
    async def exists(self, path: str) -> bool: ...
