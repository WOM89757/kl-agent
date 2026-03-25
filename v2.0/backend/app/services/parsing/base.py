from abc import ABC, abstractmethod
from typing import List
from app.services.chunking.models import Block


class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path) -> List[Block]:
        raise NotImplementedError
