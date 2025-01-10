from helpers.conversation import load_conversations, summarise_conversation
from helpers.clusters import cluster_summaries, reduce_clusters, embed_summaries
from asyncio import run, Semaphore
import instructor
import google.generativeai as genai
from tqdm.asyncio import tqdm_asyncio as asyncio
from rich import print
import json
import os
from openai import AsyncOpenAI

from helpers.types import Cluster


async def generate_clusters(
    SUMMARIES_PER_CLUSTER=20,
    CHILD_CLUSTERS_PER_CLUSTER=10,
    MAX_FINAL_CLUSTERS=10,
    start_step=None,
):
    conversations = load_conversations("conversations.json")

    # Step 1: Generate or load summaries
    if start_step == "summarize" or not os.path.exists("checkpoints/summaries.json"):
        client = instructor.from_gemini(
            genai.GenerativeModel("gemini-1.5-flash-latest"),
            use_async=True,
        )
        sem = Semaphore(50)

        summaries = await asyncio.gather(
            *[
                summarise_conversation(client, sem, conversation)
                for conversation in conversations
            ]
        )

        # Save summaries
        with open("checkpoints/summaries.json", "w") as f:
            for summary in summaries:
                f.write(json.dumps(summary) + "\n")
        print("Generated and saved summaries")
    else:
        with open("checkpoints/summaries.json", "r") as f:
            summaries = [json.loads(line) for line in f]
        print("Loaded existing summaries")

    # Step 2: Generate or load embeddings
    if start_step in ["summarize", "embed"] or not os.path.exists(
        "checkpoints/embedded_summaries.json"
    ):
        oai_client = AsyncOpenAI()
        sem = Semaphore(10)
        await embed_summaries(oai_client, sem, summaries)
        print("Generated and saved embeddings")

    # Step 3: Generate or load base clusters
    if start_step in ["summarize", "embed", "cluster"] or not os.path.exists(
        "checkpoints/base_clusters.json"
    ):
        client = instructor.from_gemini(
            genai.GenerativeModel("gemini-1.5-flash-latest"),
            use_async=True,
        )
        sem = Semaphore(10)

        base_clusters = await cluster_summaries(
            client, sem, summaries, SUMMARIES_PER_CLUSTER
        )

        # Save base clusters
        with open("checkpoints/base_clusters.json", "w") as f:
            for cluster in base_clusters:
                f.write(cluster.model_dump_json() + "\n")
        print(f"Generated and saved {len(base_clusters)} base clusters")
    else:
        with open("checkpoints/base_clusters.json", "r") as f:
            base_clusters = [Cluster.model_validate_json(line) for line in f]
        print("Loaded existing base clusters")

    # Create checkpoints directory if it doesn't exist
    os.makedirs("checkpoints", exist_ok=True)

    clusters = base_clusters
    root_clusters = base_clusters
    iteration = 0

    while len(root_clusters) >= MAX_FINAL_CLUSTERS:
        print(f"\nIteration {iteration}")
        print(f"Starting with {len(root_clusters)} root clusters")

        # Get both updated original clusters and new parent clusters
        reduced_clusters = await reduce_clusters(
            client, sem, root_clusters, CHILD_CLUSTERS_PER_CLUSTER
        )

        # Recalculate root clusters for next iteration
        root_clusters = [c for c in reduced_clusters if not c.parent_id]

        # Remove the outdated versions of clusters that were just reduced
        old_cluster_ids = {rc.id for rc in root_clusters}
        clusters = [c for c in clusters if c.id not in old_cluster_ids]

        # Add both the updated original clusters and new parent clusters
        clusters.extend(reduced_clusters)

        print(f"Reduced to {len(root_clusters)} root clusters")
        print(f"Total clusters after reduction: {len(clusters)}")

        iteration += 1

    print(f"\nFinal reduction complete:")
    print(f"Root clusters: {len(root_clusters)}")
    print(f"Total clusters (including children): {len(clusters)}")

    # Save final clusters
    with open("clusters.json", "w") as f:
        for cluster in clusters:
            f.write(cluster.model_dump_json() + "\n")


if __name__ == "__main__":
    run(generate_clusters())
