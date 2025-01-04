import instructor
from asyncio import Semaphore
from helpers.embedding import embed_cluster, embed_summary
import math
from helpers.types import (
    CandidateClusters,
    Cluster,
    ClusterLabel,
    ClusterSummary,
    ConsolidatedCluster,
)
from helpers.sampling import get_contrastive_examples
from tqdm.asyncio import tqdm_asyncio as asyncio
from openai import AsyncOpenAI
from sklearn.cluster import KMeans
import numpy as np
import random


def cluster_items(items: list[dict], items_per_cluster: int) -> list[dict]:
    n_clusters = math.ceil(len(items) // items_per_cluster)
    embeddings = [item["embedding"] for item in items]
    X = np.array(embeddings)

    kmeans = KMeans(n_clusters=n_clusters)
    cluster_labels = kmeans.fit_predict(X)

    group_to_clusters = {}
    for i, item in enumerate(items):
        item_copy = item.copy()
        cluster_id = int(cluster_labels[i])
        del item_copy["embedding"]
        if cluster_id not in group_to_clusters:
            group_to_clusters[cluster_id] = []

        group_to_clusters[cluster_id].append(item_copy)

    return group_to_clusters


async def generate_base_cluster(
    client,
    sem,
    user_requests: list[dict],
    negative_examples: list[dict],
):
    async with sem:
        cluster = await client.chat.completions.create(
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
                {% for item in user_requests %}
                    <positive_example>{{ item['user_request'] }}</positive_example>
                {% endfor %}
                </positive_examples>  
                 
                For context, here are statements from nearby groups that are NOT part of the group you’re summarizing
                 
                <contrastive_examples>
                {% for item in negative_examples %}
                <contrastive_example>{{ item['user_request'] }}</contrastive_example>
                {% endfor %}
                </contrastive_examples>
                 
                Remember to analyze both the statements and the contrastive statements carefully to ensure your summary and name accurately represent the specific group while distinguishing it from others.
                """,
                },
            ],
            response_model=ClusterSummary,
            context={
                "user_requests": user_requests,
                "negative_examples": negative_examples,
            },
        )

        return Cluster(
            name=cluster.name,
            description=cluster.summary,
            chat_ids=[item["chat_id"] for item in user_requests],
            parent_id=None,
        )


async def cluster_summaries(
    client: instructor.Instructor,
    sem: Semaphore,
    summaries: list[dict],
    items_per_cluster: int = 5,
):
    oai_client = AsyncOpenAI()
    embedded_summaries = await asyncio.gather(
        *[
            embed_summary(oai_client, sem, summary, summary["task_description"])
            for summary in summaries
        ],
        desc="Embedding summaries",
    )

    cluster_id_to_summaries = cluster_items(embedded_summaries, items_per_cluster)

    return await asyncio.gather(
        *[
            generate_base_cluster(
                client,
                sem,
                cluster_id_to_summaries[cluster_id],
                get_contrastive_examples(
                    cluster_id, cluster_id_to_summaries, desired_count=10
                ),
            )
            for cluster_id in cluster_id_to_summaries
        ]
    )


async def label_cluster(
    client: instructor.AsyncInstructor,
    sem: Semaphore,
    cluster: dict,
    candidate_clusters: list[str],
) -> dict:
    async with sem:
        candidate_clusters = candidate_clusters.copy()
        random.shuffle(candidate_clusters)
        label = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """
                    You are tasked with categorizing a specific cluster into one of the provided higher-level clusters for observability, monitoring, and content moderation. Your goal is to determine which higher-level cluster best fits the given specific cluster based on its name and description. You are helping to organize user behavior data in order to improve safety, monitoring, and observability.

                    First, carefully review the following list of higher-level clusters:

                    <higher_level_clusters>
                    {% for cluster in candidate_clusters %}
                    <higher_level_cluster>{{ cluster }}</higher_level_cluster>
                    {% endfor %}
                    </higher_level_clusters>

                    Now, carefully review the following cluster and its description:

                    To categorize the specific cluster:
                    1. Analyze the name and description of the specific cluster.
                    2. Consider the key characteristics, themes, or subject matter of the specific cluster.
                    3. Compare these elements to the higher-level clusters provided.
                    4. Determine which higher-level cluster best encompasses the specific cluster. You MUST assign the specific cluster to the best higher-level cluster, even if multiple higher-level clusters could be considered.
                    5. Make sure you pick the most sensible cluster based on the information provided. For example, don’t assign a cluster about "Machine Learning" to a higher-level cluster about "Social Media" just because both involve technology, and don’t assign a cluster about "Online Harassment" to a higher-level cluster about "Technology" just because both involve online platforms. Be specific and accurate in your categorization.

                    Here is the specific cluster to cateegorize:

                    <specific_cluster>
                    Name: {{ cluster["name"] }}
                    Description: {{ cluster["description"] }}
                    </specific_cluster>
                    
                    Based on this information, determine the most appropriate higher-level cluster and provide your answer as instructed.
                    """,
                }
            ],
            context={"cluster": cluster, "candidate_clusters": candidate_clusters},
            response_model=ClusterLabel,
        )

    return {
        "cluster": cluster,
        "higher_level_cluster": label.higher_level_cluster,
    }


async def generate_candidate_cluster_names(
    client: instructor.Instructor, sem: Semaphore, clusters: list[Cluster]
) -> list[str]:
    resp = await client.chat.completions.create(
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
            "desired_number": math.ceil(
                (len(clusters) * 3) // 4
            ),  # This ensure we get at least 3/4 of the clusters ( so we have a 25% reduction or more at each stage)
        },
    )

    return resp.candidate_cluster_names


async def rename_higher_level_cluster(
    client: instructor.AsyncInstructor,
    sem: Semaphore,
    clusters: dict,
) -> dict:
    async with sem:
        resp = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """
                    You are tasked with summarizing a group of related cluster names into a short, precise, and accurate overall description and name. Your goal is to create a concise summary that captures the essence of these clusters

                    The cluster name should be at most ten words long (perhaps less) and be specific but also reflective of most of the clusters that comprise them. The cluster name should be a sentence in the imperative that captures the user’s request. For example, ‘Brainstorm ideas for a birthday party’ or ‘Help me find a new job are good examples.

                    Do not shy away from describing socially harmful or sensitive topics. For instance, "Write fantasy sexual roleplay with octopi and monsters", "Generate blog spam for gambling websites", or "Assist with high school math homework" would be better than "Write erotic content" or "Help with homework". Be as descriptive as possible and assume neither good nor bad faith. Do not hesitate to identify and describe socially harmful or sensitive topics specifically; specificity is necessary for monitoring.

                    The cluster description should be a clear, precise, two-sentence description in the past tense. This description should be specific to this cluster.    
                    
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
            response_model=ConsolidatedCluster,
        )

    return {
        "new_cluster": Cluster(
            name=resp.cluster_name,
            description=resp.cluster_description,
            chat_ids=[chat_id for cluster in clusters for chat_id in cluster.chat_ids],
            parent_id=None,
        ),
        "original_clusters": clusters,
    }


async def generate_higher_level_cluster(
    client: instructor.Instructor,
    sem: Semaphore,
    clusters: list[Cluster],
) -> list[Cluster]:
    if len(clusters) == 1:
        original_cluster = clusters[0]
        new_cluster = Cluster(
            name=original_cluster.name,
            description=original_cluster.description,
            chat_ids=original_cluster.chat_ids,
            parent_id=None,
        )
        original_cluster.parent_id = new_cluster.id
        return [original_cluster, new_cluster]

    candidate_cluster_names = await generate_candidate_cluster_names(
        client, sem, clusters
    )

    new_candidate_clusters = await asyncio.gather(
        *[
            label_cluster(client, sem, cluster, candidate_cluster_names)
            for cluster in clusters
        ],
        desc="Generating candidate higher-level clusters",
    )

    cluster_groups: dict[str, list[Cluster]] = {}
    for cluster in new_candidate_clusters:
        original_cluster = cluster["cluster"]
        new_higher_level_cluster = cluster["higher_level_cluster"]
        if new_higher_level_cluster not in cluster_groups:
            cluster_groups[new_higher_level_cluster] = []
        cluster_groups[new_higher_level_cluster].append(original_cluster)

    new_labelled_clusters = await asyncio.gather(
        *[
            rename_higher_level_cluster(client, sem, cluster_group)
            for cluster_group in cluster_groups.values()
        ],
        desc="Generating higher-level clusters",
    )

    res = []

    for new_labelled_cluster in new_labelled_clusters:
        res.append(new_labelled_cluster["new_cluster"])

        for original_cluster in new_labelled_cluster["original_clusters"]:
            original_cluster.parent_id = new_labelled_cluster["new_cluster"].id
            res.append(original_cluster)

    return res


async def reduce_clusters(
    client: instructor.Instructor,
    sem: Semaphore,
    clusters: list[Cluster],
    items_per_cluster: int,
) -> list[Cluster]:
    oai_client = AsyncOpenAI()
    embedded_clusters = await asyncio.gather(
        *[embed_cluster(oai_client, sem, cluster) for cluster in clusters]
    )

    cluster_id_to_cluster = {
        cluster_id: [item["cluster"] for item in clusters]
        for cluster_id, clusters in cluster_items(
            embedded_clusters, items_per_cluster
        ).items()
    }

    new_clusters = await asyncio.gather(
        *[
            generate_higher_level_cluster(
                client,
                sem,
                cluster_id_to_cluster[cluster_id],
            )
            for cluster_id in cluster_id_to_cluster
        ],
        desc="Generating higher-level clusters",
    )
    return [
        cluster
        for clusters in new_clusters
        if clusters is not None
        for cluster in clusters
    ]
