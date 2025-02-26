import asyncio
from openai import AsyncOpenAI
import pandas as pd
import vertexai
import instructor
import vertexai.generative_models
import os

from pathlib import Path
from uuid import uuid4
from datetime import datetime
from asyncio import run


from kura import Kura
# from kura.cluster import ClusterModel
from kura.non_async.summarisation import SummaryModel
from kura.embedding import OpenAIEmbeddingModel
from kura.dimensionality import HDBUMAP
from kura.types import Conversation, Message

# vertexai.init()

        


def load_conversation_data(file_path, sample_size=None):
    """Load conversation data from CSV and convert to Kura Conversation objects.
    
    Args:
        file_path: Path to the CSV file containing conversation data
        sample_size: Maximum number of conversations to process
        
    Returns:
        List of Kura Conversation objects
    """
    # Load the CSV data
    df = pd.read_csv(file_path)
    
    # Group by conversation ID
    grouped = df.groupby("conversationId")
    
    all_conversations = []
    count = 0
    
    # Process each conversation group
    for convo_id, group in grouped:
        messages = []
        
        # Process each message in the conversation
        for _, row in group.iterrows():
            # Create and add user message
            user_message = Message(
                created_at=row["queryDatetime"],
                role="user",
                content=row["query"],
                id=row["_id"],
            )
            
            # Create and add assistant message
            assistant_message = Message(
                created_at=row["queryDatetime"],
                role="assistant",
                content=row["response"],
                id=row["_id"],
            )
            
            messages.append(user_message)
            messages.append(assistant_message)
        
        # Create a Conversation object for this group
        current_convo = Conversation(
            messages=messages,
            chat_id=convo_id,
            created_at=datetime.now(),
        )
        
        all_conversations.append(current_convo)
        count += 1
        
        # Stop after reaching the sample size
        if sample_size is not None:
            if count >= sample_size:
                break
            
    return all_conversations


# def initialize_kura_engine(output_dir, max_clusters):
#     cluster_model = ClusterModel(
#         client=instructor.from_vertexai(
#             vertexai.generative_models.GenerativeModel("gemini-1.5-flash-001"),
#             _async=True,
#             mode=instructor.Mode.VERTEXAI_TOOLS)

#         # client = instructor.from_openai(
#         #     AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
#         #     # use_async=True,
#         #     )
#         )

#     """Initialize and return a configured Kura engine."""
#     return Kura(
#         embedding_model=OpenAIEmbeddingModel(),
#         cluster_model=cluster_model,
#         summarisation_model=SummaryModel(),
#         dimensionality_reduction=HDBUMAP(),        
#         max_clusters=max_clusters,
#         checkpoint_dir=output_dir
#     )


async def main():
    """Main execution function."""
    # Prepare the output directory
    output_folder_path = Path("../kura/data/aibots_conversations/summaries")
    output_folder_path.mkdir(parents=True, exist_ok=True)
    
    # Load conversation data
    file_path = "~/efs/data/aibots/AIBOTS_CONVERSATIONS/AIBOTS_ANALYTICS/PLAYGROUND.csv"
    conversations = load_conversation_data(file_path, sample_size=None)
    
    # # Initialize Kura engine
    # kura = initialize_kura_engine(output_folder_path, max_clusters=300)
    
    # # Cluster conversations
    # run(kura.cluster_conversations(conversations))

    summary_model = SummaryModel()
    await summary_model.summarise(conversations, output_folder_path)

if __name__ == "__main__":
    asyncio.run(main())
    # main()