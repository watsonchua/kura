from kura.embedding import OpenAIEmbeddingModel
import json
import asyncio
import tqdm
from asyncio import Semaphore

def main():
    embedding_model = OpenAIEmbeddingModel()
    
    async def process_batch(batch, batch_num, total_batches):
        results = []
        # Adding tqdm progress bar for each item within the batch
        for data in tqdm.tqdm(batch, desc=f"Batch {batch_num}/{total_batches}", leave=False):
            embeddings = await embedding_model.embed(data["summary"], Semaphore(10))
            results.append({**data, "embeddings": embeddings})
        return results
    
    async def main_async():
        # Read all lines into memory
        with open("/home/watsonchua/work/kura/data/aibots_conversations/summaries/summaries.jsonl", "r") as f:
            lines = [json.loads(line) for line in f]
        
        # Process in batches of 100
        batches = [lines[i:i+100] for i in range(0, len(lines), 100)]
        total_batches = len(batches)
        
        # Open the output file in append mode
        with open("/home/watsonchua/work/kura/data/aibots_conversations/summaries/embeddings.jsonl", "a") as f:
            for batch_num, batch in enumerate(tqdm.tqdm(batches, desc="Processing batches"), 1):
                batch_results = await process_batch(batch, batch_num, total_batches)
                # Write results for this batch immediately
                for item in batch_results:
                    f.write(json.dumps(item) + "\n")
                # Flush to ensure data is written to disk
                f.flush()
    
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
