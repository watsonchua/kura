from openai import AsyncOpenAI
from asyncio import Semaphore
from helpers.types import Cluster


async def embed_summary(
    oai_client: AsyncOpenAI, sem: Semaphore, item: str, text_to_embed: str
) -> list[float]:
    return {
        "embedding": (
            await oai_client.embeddings.create(
                input=text_to_embed, model="text-embedding-3-small"
            )
        )
        .data[0]
        .embedding,
        **item,
    }


async def embed_cluster(
    oai_client: AsyncOpenAI, sem: Semaphore, cluster: Cluster
) -> list[float]:
    return {
        "embedding": (
            await oai_client.embeddings.create(
                input=f"""
                Name: {cluster.name}
                Description: {cluster.description}
                """,
                model="text-embedding-3-small",
            )
        )
        .data[0]
        .embedding,
        "cluster": cluster,
    }
