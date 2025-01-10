from asyncio import Semaphore
from kura.types import ConversationSummary, GeneratedCluster, Cluster
from instructor import from_gemini
import google.generativeai as genai
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm_asyncio as asyncio
import numpy as np
from sklearn.cluster import KMeans
import math
import os
import json


class SummaryCluster:
    def __init__(
        self,
        cluster_model=from_gemini(
            genai.GenerativeModel("gemini-1.5-flash-latest"), use_async=True
        ),
        embedding_model=AsyncOpenAI(),
        max_concurrent_calls: int = 40,
        summaries_per_cluster: int = 10,
        checkpoint_dir: str = "checkpoints",
        checkpoint_file_name: str = "base_clusters.json",
    ):
        self.sem = Semaphore(max_concurrent_calls)
        self.cluster_model = cluster_model
        self.embedding_model = embedding_model
        self.summaries_per_cluster = summaries_per_cluster
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_file_name = checkpoint_file_name

    async def _embed(self, summary: ConversationSummary):
        async with self.sem:
            embedding = await self.embedding_model.embeddings.create(
                input=summary.user_request,
                model="text-embedding-3-small",
            )
            return {
                "item": summary,
                "embedding": embedding.data[0].embedding,
            }

    async def cluster_summaries(
        self, summaries: list[ConversationSummary]
    ) -> dict[int, list[ConversationSummary]]:
        n_clusters = math.ceil(len(summaries) / self.summaries_per_cluster)
        embeddings = [summary["embedding"] for summary in summaries]
        X = np.array(embeddings)

        kmeans = KMeans(n_clusters=n_clusters)
        cluster_labels = kmeans.fit_predict(X)

        group_to_clusters = {}
        for i, summary in enumerate(summaries):
            cluster_id = int(cluster_labels[i])
            if cluster_id not in group_to_clusters:
                group_to_clusters[cluster_id] = []
            group_to_clusters[cluster_id].append(summary["item"])

        return group_to_clusters

    def get_contrastive_examples(
        self,
        cluster_id: int,
        cluster_id_to_summaries: dict[int, list[ConversationSummary]],
        desired_count: int = 10,
    ):
        other_clusters = [c for c in cluster_id_to_summaries.keys() if c != cluster_id]
        all_examples = []
        for cluster in other_clusters:
            all_examples.extend(cluster_id_to_summaries[cluster])

        # If we don't have enough examples, return all of them
        if len(all_examples) <= desired_count:
            return all_examples

        # Otherwise sample without replacement
        return list(np.random.choice(all_examples, size=desired_count, replace=False))

    async def generate_base_cluster(
        self,
        cluster_id: int,
        cluster_id_to_summaries: dict[int, list[ConversationSummary]],
    ):
        async with self.sem:
            contrastive_examples = self.get_contrastive_examples(
                cluster_id, cluster_id_to_summaries
            )
            positive_examples = cluster_id_to_summaries[cluster_id]
            cluster = await self.cluster_model.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": """
                    You are tasked with summarizing a group of related statements into a short, precise, and accurate description and name. Your goal is to create a concise summary that captures the essence of these statements and distinguishes them from other similar groups of statements.
                    
                    Summarize all the statements into a clear, precise, two-sentence description in the past tense. Your summary should be specific to this group and distinguish it from the contrastive answers of the other groups.

                    After creating the summary, generate a short name for the group of statements. This name should be at most ten words long (perhaps less) and be specific but also reflective of most of the statements (rather than reflecting only one or two). The name should distinguish this group from the contrastive examples. For instance, "Write fantasy sexual roleplay with octopi and monsters", "Generate blog spam for gambling websites", or "Assist with high school math homework" would be better and more actionable than general terms like "Write erotic content" or "Help with homework". Be as descriptive as possible and assume neither good nor bad faith. Do not hesitate to identify and describe socially harmful or sensitive topics specifically; specificity is necessary for monitoring
                    
                    The cluster name should be a sentence in the imperative that captures the user’s request. For example, ‘Brainstorm ideas for a birthday party’ or ‘Help me find a new job.”
                    """,
                    },
                    {
                        "role": "user",
                        "content": """
                    Here are the relevant statements

                    Below are the related statements:
                    <positive_examples>
                    {% for item in positive_examples %}
                        <positive_example>{{ item.user_request }}</positive_example>
                    {% endfor %}
                    </positive_examples>  
                    
                    For context, here are statements from nearby groups that are NOT part of the group you’re summarizing
                    
                    <contrastive_examples>
                    {% for item in contrastive_examples %}
                    <contrastive_example>{{ item.user_request }}</contrastive_example>
                    {% endfor %}
                    </contrastive_examples>
                    
                    Remember to analyze both the statements and the contrastive statements carefully to ensure your summary and name accurately represent the specific group while distinguishing it from others.
                    """,
                    },
                ],
                response_model=GeneratedCluster,
                context={
                    "positive_examples": positive_examples,
                    "contrastive_examples": contrastive_examples,
                },
            )

            return Cluster(
                name=cluster.name,
                description=cluster.summary,
                chat_ids=[item.chat_id for item in positive_examples],
                parent_id=None,
            )

    async def embed_summaries(self, summaries: list[ConversationSummary]):
        coros = [self._embed(summary) for summary in summaries]
        return await asyncio.gather(*coros, desc="Embedding Summaries")

    def save_checkpoint(self, data: list[ConversationSummary]):
        with open(
            os.path.join(self.checkpoint_dir, self.checkpoint_file_name), "w"
        ) as f:
            for item in data:
                f.write(item.model_dump_json() + "\n")

    def load_checkpoint(self) -> list[ConversationSummary]:
        with open(
            os.path.join(self.checkpoint_dir, self.checkpoint_file_name), "r"
        ) as f:
            return [Cluster(**json.loads(line)) for line in f]

    def save_checkpoint_clusters(self, clusters: list[Cluster]):
        with open(
            os.path.join(self.checkpoint_dir, self.checkpoint_file_name), "w"
        ) as f:
            for cluster in clusters:
                f.write(cluster.model_dump_json() + "\n")

    async def cluster_conversation_summaries(
        self, summaries: list[ConversationSummary]
    ) -> list[Cluster]:
        # Load Checkpoint By Default
        if os.path.exists(os.path.join(self.checkpoint_dir, self.checkpoint_file_name)):
            print("Loading Base Cluster Checkpoint")
            return self.load_checkpoint()

        embedded_summaries = await self.embed_summaries(summaries)
        cluster_id_to_summaries = await self.cluster_summaries(embedded_summaries)
        clusters = await asyncio.gather(
            *[
                self.generate_base_cluster(cluster_id, cluster_id_to_summaries)
                for cluster_id in cluster_id_to_summaries.keys()
            ],
            desc="Generating Base Clusters",
        )
        self.save_checkpoint(clusters)
        return clusters
