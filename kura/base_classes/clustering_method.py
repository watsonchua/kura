from abc import ABC, abstractmethod
from typing import TypeVar, Union

T = TypeVar("T")


class BaseClusteringMethod(ABC):
    @abstractmethod
    def cluster(
        self, items: list[dict[str, Union[T, list[float]]]]
    ) -> dict[int, list[T]]:
        pass
