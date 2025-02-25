from kura.base_classes import BaseEmbeddingModel
from asyncio import Semaphore, wait_for
from tenacity import retry, wait_fixed, stop_after_attempt
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


class OpenAIEmbeddingModel(BaseEmbeddingModel):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"])

    @retry(wait=wait_fixed(3), stop=stop_after_attempt(3))
    async def embed(self, text: str, sem: Semaphore) -> list[float]:
        async with sem:
            resp = await wait_for(
                self.client.embeddings.create(
                    input=text, model="text-embedding-3-small-eastus"
                ),
                timeout=5,
            )
            return resp.data[0].embedding
