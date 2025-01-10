from .types import Cluster, GeneratedCluster
from openai import AsyncOpenAI
from asyncio import Semaphore
from tqdm.asyncio import tqdm_asyncio as asyncio
import math
import re
import random
import numpy as np
from sklearn.cluster import KMeans
from pydantic import BaseModel, field_validator, ValidationInfo
from instructor import from_gemini, AsyncInstructor
import google.generativeai as genai


class CandidateClusters(BaseModel):
    candidate_cluster_names: list[str]

    @field_validator("candidate_cluster_names")
    def validate_candidate_cluster_names(
        cls, v: list[str], info: ValidationInfo
    ) -> list[str]:
        if len(v) == 0:
            raise ValueError("Candidate cluster names must be a non-empty list")

        v = [label.strip() for label in v]
        v = [label[:-1] if label.endswith(".") else label for label in v]

        return [re.sub(r"\\{1,}", "", label.replace('"', "")) for label in v]


class ClusterLabel(BaseModel):
    higher_level_cluster: str

    @field_validator("higher_level_cluster")
    def validate_higher_level_cluster(cls, v: str, info: ValidationInfo) -> str:
        if v not in info.context["candidate_clusters"]:
            raise ValueError(
                f"""
                Invalid higher-level cluster: |{v}|
                
                Valid clusters are:
                {', '.join(f'|{c}|' for c in info.context['candidate_clusters'])}
                """
            )
        return v


class ClusterModel:
    def __init__(
        self,
        embed_model: AsyncOpenAI = AsyncOpenAI(),
        cluster_model: AsyncInstructor = from_gemini(
            genai.GenerativeModel("gemini-1.5-flash-latest"), use_async=True
        ),
        max_concurrent_calls: int = 40,
        base_cluster_per_cluster: int = 20,
    ) -> None:
        self.sem = Semaphore(max_concurrent_calls)
        self.embed_model = embed_model
        self.cluster_model = cluster_model
        self.base_cluster_per_cluster = base_cluster_per_cluster

    async def embed_cluster(self, cluster: Cluster) -> Cluster:
        async with self.sem:
            embedding = await self.embed_model.embeddings.create(
                input=f"""
                Name: {cluster.name}
                Description: {cluster.description}
                """,
                model="text-embedding-3-small",
            )
            return {
                "item": cluster,
                "embedding": embedding.data[0].embedding,
            }

    def cluster_base_clusters(
        self, clusters: list[Cluster]
    ) -> dict[int, list[Cluster]]:
        n_clusters = math.ceil(len(clusters) / self.base_cluster_per_cluster)

        if n_clusters == 1:
            return {0: [item["item"] for item in clusters]}

        embeddings = [item["embedding"] for item in clusters]
        X = np.array(embeddings)

        kmeans = KMeans(n_clusters=n_clusters)
        cluster_labels = kmeans.fit_predict(X)

        group_to_clusters = {}
        for i, item in enumerate(clusters):
            cluster_id = int(cluster_labels[i])
            if cluster_id not in group_to_clusters:
                group_to_clusters[cluster_id] = []

            group_to_clusters[cluster_id].append(item["item"])

        return group_to_clusters

    async def generate_candidate_cluster_names(
        self, clusters: list[Cluster]
    ) -> list[str]:
        async with self.sem:
            resp = await self.cluster_model.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": """
                You are tasked with creating higher-level cluster names based on a given list of clusters and their descriptions. Your goal is to come up with broader categories that could encompass one or more of the provided clusters

                First, review the list of clusters and their descriptions:
                <cluster_list>
                    {% for cluster in clusters %}
                    <cluster>{{ cluster.name }}: {{ cluster.description }}</cluster>
                    {% endfor %}
                </cluster_list>

                Your task is to create at most {{ desired_number }} higher-level cluster names that could potentially include one or more of the provided clusters. These higher-level clusters should represent broader categories or themes that emerge from the given clusters, while remaining as specific as possible. If there are many clusters with a specific theme, ensure that the higher-level cluster name remains the maximum level of specificity. You are helping to organize user behavior data in order to improve safety, monitoring, and observability. You can generate less than {{ desired_number }} names if you feel that fewer are appropriate and accurately capture the clusters. 

                Guidelines for creating higher-level clusters names
                1. Analyze the themes, topics or characteristics common to multiple clusters.
                2. Create names that are specific enough to be meaningful but but not so specific that they can’t meaningfully represent many different clusters. Avoid overly general or vague terms, and do not hesitate to describe socially harmful or sensitive topics (in fact, clusters that clearly describe harmful behavior are slightly preferred); specificity is necessary for observability and enforcement.
                3. Ensure that the higher-level cluster names are distinct from one another.
                4. Use clear, concise, and descriptive language for the cluster names. Assume neither good nor bad faith for the content in the clusters.

                Think about the relationships between the given clusters and potential overarching themes. 
                
                Focus on creating meaningful, distinct and precise ( but not overly specific ) higher-level cluster names that could encompass multiple sub-clusters.
                """,
                    }
                ],
                response_model=CandidateClusters,
                context={
                    "clusters": clusters,
                    "desired_number": math.ceil(len(clusters) / 2),
                },
                max_retries=3,
            )
            return resp.candidate_cluster_names

    async def label_cluster(
        self,
        cluster: Cluster,
        candidate_clusters: list[str],
    ) -> dict:
        async with self.sem:
            candidate_clusters = candidate_clusters.copy()
            random.shuffle(candidate_clusters)
            label = await self.cluster_model.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": """
                        You are tasked with categorizing a specific cluster into one of the provided higher-level clusters for observability, monitoring, and content moderation. Your goal is to determine which higher-level cluster best fits the given specific cluster based on its name and description.

                        First, here are the ONLY valid higher-level clusters you may select from:
                        <higher_level_clusters>
                        {% for cluster in candidate_clusters %}
                        <higher_level_cluster>{{ cluster }}</higher_level_cluster>
                        {% endfor %}
                        </higher_level_clusters>

                        Here is the specific cluster to categorize:
                        <specific_cluster>
                        Name: {{ cluster["name"] }}
                        Description: {{ cluster["description"] }}
                        </specific_cluster>

                        RULES:
                        1. You MUST select EXACTLY ONE higher-level cluster from the provided list
                        2. You MUST output the higher-level cluster name EXACTLY as written - no modifications allowed
                        3. You MUST NOT create new cluster names or combinations
                        4. You MUST NOT output any additional text or explanations
                        5. You MUST NOT use partial matches or approximate names

                        CLASSIFICATION PROCESS:
                        1. First, record the exact list of valid higher-level clusters
                        2. Read the specific cluster's name and description carefully
                        3. Compare the specific cluster's key characteristics against each valid higher-level cluster
                        4. Select the single most appropriate higher-level cluster that encompasses the specific cluster
                        5. Verify your selected cluster exactly matches one from the valid list
                        6. Output ONLY the selected higher-level cluster name, exactly as it appeared in the valid list

                        Here is the specific cluster to categorize:

                        <specific_cluster>
                        Name: {{ cluster["name"] }}
                        Description: {{ cluster["description"] }}
                        </specific_cluster>
                        
                        Based on this information, determine the most appropriate higher-level cluster and provide your answer as instructed.
                        """,
                    }
                ],
                context={
                    "cluster": cluster,
                    "candidate_clusters": candidate_clusters,
                },
                response_model=ClusterLabel,
                max_retries=3,
            )
        return {
            "cluster": cluster,
            "higher_level_cluster": label.higher_level_cluster,
        }

    async def rename_cluster_group(self, clusters: list[Cluster]) -> Cluster:
        async with self.sem:
            resp = await self.cluster_model.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": """
                        You are tasked with summarizing a group of related cluster names into a short, precise, and accurate overall description and name. Your goal is to create a concise summary that captures the essence of these clusters

                        The cluster name should be at most ten words long (perhaps less) and be specific but also reflective of most of the clusters that comprise them. The cluster name should be a sentence in the imperative that captures the user’s request. For example, ‘Brainstorm ideas for a birthday party’ or ‘Help me find a new job are good examples.

                        Do not shy away from describing socially harmful or sensitive topics. For instance, "Write fantasy sexual roleplay with octopi and monsters", "Generate blog spam for gambling websites", or "Assist with high school math homework" would be better than "Write erotic content" or "Help with homework". Be as descriptive as possible and assume neither good nor bad faith. Do not hesitate to identify and describe socially harmful or sensitive topics specifically; specificity is necessary for monitoring.

                        The cluster description should be a clear, precise, two-sentence description in the past tense. This description should be specific to this cluster. Make sure that you've captured the most important details of the cluster.
                        
                        Below are the related cluster names
                        <clusters>
                            {% for cluster in clusters %}
                                <cluster>{{ cluster.name }}: {{ cluster.description }}</cluster>
                            {% endfor %}
                        </clusters>

                        Ensure your summary and name accurately represent the clusters and are specific to the clusters.
                        """,
                    }
                ],
                context={"clusters": clusters},
                response_model=GeneratedCluster,
            )

        res = []

        new_cluster = Cluster(
            name=resp.name,
            description=resp.summary,
            chat_ids=[chat_id for cluster in clusters for chat_id in cluster.chat_ids],
            parent_id=None,
        )

        res.append(new_cluster)

        for cluster in clusters:
            res.append(
                Cluster(
                    id=cluster.id,
                    name=cluster.name,
                    description=cluster.description,
                    chat_ids=cluster.chat_ids,
                    parent_id=new_cluster.id,
                )
            )

        return res

    async def generate_higher_level_cluster(
        self, clusters: list[Cluster]
    ) -> list[Cluster]:
        """
        This takes in a list of clusters and generates a smaller list of clusters that are more general.

        We do so in a 3 step process

        1. First we generate a list of candidate cluster names
        2. Then we label each base cluster with a potential candidate cluster name
        3. Lastly, for our new clusters, we then generate a new re-labelled cluster with a new title and description that is more representative of these new clusters

        We do have a base case, in which that if a cluster contains a single item, it's just returned as is.
        """
        if len(clusters) == 1:
            return clusters

        candidates_cluster_names = await self.generate_candidate_cluster_names(clusters)

        labelled_clusters = await asyncio.gather(
            *[
                self.label_cluster(cluster, candidates_cluster_names)
                for cluster in clusters
            ],
            disable=True,
        )
        label_to_cluster = {}
        for labelled_cluster in labelled_clusters:
            if labelled_cluster["higher_level_cluster"] not in label_to_cluster:
                label_to_cluster[labelled_cluster["higher_level_cluster"]] = []

            label_to_cluster[labelled_cluster["higher_level_cluster"]].append(
                labelled_cluster["cluster"]
            )

        new_clusters = await asyncio.gather(
            *[
                self.rename_cluster_group(cluster)
                for cluster in label_to_cluster.values()
            ],
            disable=True,
        )

        final_clusters = []

        for clusters in new_clusters:
            final_clusters.extend(clusters)

        return final_clusters

    async def cluster_clusters(self, clusters: list[Cluster]) -> list[Cluster]:
        embedded_clusters = await asyncio.gather(
            *[self.embed_cluster(cluster) for cluster in clusters], disable=True
        )
        clusters = self.cluster_base_clusters(embedded_clusters)
        new_clusters = await asyncio.gather(
            *[
                self.generate_higher_level_cluster(cluster)
                for cluster in clusters.values()
            ],
            desc="Generating New Higher Level Clusters",
        )

        res = []
        for clusters in new_clusters:
            res.extend(clusters)

        return res
