from .summarise import SummariseBase
from .summary_cluster import SummaryCluster
from .types import Cluster, Conversation, Message
import json
import os
from .cluster import ClusterModel


class LLMCluster:
    def __init__(
        self,
        summariser: SummariseBase = SummariseBase(),
        base_cluster_model: SummaryCluster = SummaryCluster(),
        cluster_model: ClusterModel = ClusterModel(),
        max_clusters: int = 10,
        checkpoint_dir: str = "checkpoints",
    ):
        self.summariser = summariser
        self.base_cluster_model = base_cluster_model
        self.max_clusters = max_clusters
        self.checkpoint_dir = checkpoint_dir
        self.cluster_model = cluster_model
        
        self.clusters = []

        if not os.path.exists(self.checkpoint_dir):
            os.makedirs(self.checkpoint_dir)

    async def reduce_clusters(
        self, clusters: list[Cluster], root_clusters: list[Cluster], iteration: int = 1
    ):
        while len(root_clusters) > self.max_clusters:
            print(f"\n=== Iteration {iteration} ===")
            print(f"    Starting with {len(root_clusters)} root clusters...")

            # Generate new parent clusters from current level
            new_parent_clusters = await self.cluster_model.cluster_clusters(
                root_clusters
            )

            # This is the new layer
            root_clusters = [c for c in new_parent_clusters if not c.parent_id]

            # Remove the outdated versions of clusters that were just reduced
            old_cluster_ids = {rc.id for rc in new_parent_clusters if rc.parent_id}
            clusters = [c for c in clusters if c.id not in old_cluster_ids]

            # Add both the updated original clusters and new parent clusters
            clusters.extend(new_parent_clusters)
            print(f"    Successfully reduced to {len(root_clusters)} root clusters")

            iteration += 1

        return clusters, root_clusters

    async def cluster_conversations(self):
        summarized_conversations = await self.summariser.summarise_conversations(
            self.conversations
        )

        base_clusters = await self.base_cluster_model.cluster_conversation_summaries(
            summarized_conversations
        )

        clusters_path = os.path.join(self.checkpoint_dir, "clusters.json")

        if os.path.exists(clusters_path):
            with open(clusters_path, "r") as f:
                clusters = [Cluster.model_validate_json(line) for line in f]
        else:
            clusters = base_clusters
            root_clusters = base_clusters

            clusters, root_clusters = await self.reduce_clusters(
                clusters, root_clusters
            )

            # Save final clusters to checkpoint directory

            with open(clusters_path, "w") as f:
                for cluster in clusters:
                    f.write(cluster.model_dump_json() + "\n")

            
        

        print(f"\nSaved {len(clusters)} total clusters to {clusters_path}")
        
        return clusters

    def load_claude_messages(
        self, path: str, max_conversations: int = -1
    ) -> list[Conversation]:
        with open(path, "r") as f:
            conversations = []
            for conversation in json.load(f):
                conversations.append(
                    Conversation(
                        chat_id=conversation["uuid"],
                        created_at=conversation["created_at"],
                        messages=[
                            Message(
                                created_at=message["created_at"],
                                role=message["sender"],
                                content="\n".join(
                                    [
                                        item["text"]
                                        for item in message["content"]
                                        if item["type"] == "text"
                                    ]
                                ),
                            )
                            for message in conversation["chat_messages"]
                        ],
                    )
                )
            self.conversations = (
                conversations
                if max_conversations == -1
                else conversations[:max_conversations]
            )
            print(f"Read in {len(self.conversations)} conversations")
