from dataclasses import dataclass
from typing import Optional


@dataclass
class Package:
    name: str
    id: str
    version: str
    source: str
    is_installed: bool = True
    available_version: Optional[str] = None
    description: Optional[str] = None

    @property
    def has_update(self) -> bool:
        return self.available_version is not None and self.available_version != self.version

    def __str__(self) -> str:
        return f"{self.name} ({self.id}) v{self.version}"