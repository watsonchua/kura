from helpers.conversation import load_conversations, summarise_conversation
from helpers.clusters import cluster_summaries, reduce_clusters
from asyncio import run, Semaphore
import instructor
import google.generativeai as genai
from tqdm.asyncio import tqdm_asyncio as asyncio
from rich import print


async def generate_clusters(
    SUMMARIES_PER_CLUSTER=20,
    CHILD_CLUSTERS_PER_CLUSTER=10,
    MAX_FINAL_CLUSTERS=10,
):
    conversations = load_conversations("conversations.json")

    client = instructor.from_gemini(
        genai.GenerativeModel("gemini-1.5-flash-latest"),
        use_async=True,
    )

    sem = Semaphore(50)

    # First we generate the summaries

    summaries = await asyncio.gather(
        *[
            summarise_conversation(client, sem, conversation)
            for conversation in conversations
        ]
    )

    base_clusters = await cluster_summaries(
        client, sem, summaries, SUMMARIES_PER_CLUSTER
    )

    print(f"Generated {len(base_clusters)} clusters")

    clusters = base_clusters
    root_clusters = base_clusters

    while len(root_clusters) >= MAX_FINAL_CLUSTERS:
        # Get both updated original clusters and new parent clusters
        reduced_clusters = await reduce_clusters(
            client, sem, root_clusters, CHILD_CLUSTERS_PER_CLUSTER
        )
        # Recalculate root clusters for next iteration
        root_clusters = [c for c in reduced_clusters if not c.parent_id]

        # Remove the outdated versions of clusters that were just reduced
        clusters = [c for c in clusters if c.id not in {rc.id for rc in root_clusters}]

        # Add both the updated original clusters and new parent clusters
        clusters.extend(reduced_clusters)

        print(
            f"Reduced {len(reduced_clusters) - len(root_clusters)} -> {len(root_clusters)} clusters"
        )

    print(f"Reduced to {len(root_clusters)} root clusters")

    # # Then we just dump the final list of clusters into a json file
    with open("clusters.json", "w") as f:
        for cluster in clusters:
            f.write(cluster.model_dump_json() + "\n")


if __name__ == "__main__":
    run(generate_clusters())
