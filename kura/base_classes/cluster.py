from abc import ABC, abstractmethod
from kura.types import Cluster, ConversationSummary


class BaseClusterModel(ABC):
    @abstractmethod
    def cluster_summaries(self, summaries: list[ConversationSummary]) -> list[Cluster]:
        pass

    # TODO : Add abstract method for hooks here once we start supporting it
