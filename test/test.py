from kura import Kura
from kura.embedding import OpenAIEmbeddingModel
from kura.summarisation import SummaryModel
from kura.dimensionality import HDBUMAP
from asyncio import run
from kura.types import Conversation, Message
from uuid import uuid4
import datetime
import pandas as pd
from pathlib import Path


output_folder_path = Path("../kura/data/aibots_conversations")
output_folder_path.mkdir(parents=True, exist_ok=True)

df = pd.read_csv("/home/watson_chua/efs/data/aibots/AIBOTS_CONVERSATIONS/AIBOTS_ANALYTICS/PLAYGROUND.csv")
grouped = df.groupby("conversationId")



from uuid import uuid4
from kura.types import Conversation, Message
import json
from datetime import datetime

all_conversations = []
sample_size = 1000
count = 0
for convo_id, group in grouped:

    messages = []
    
    for _, row in group.iterrows():
        user_message = Message(
                created_at=row["queryDatetime"],
                role="user",
                content=row["query"],
                id=row["_id"],
                )
        
        assistant_message = Message(
                created_at=row["queryDatetime"],
                role="assistant",
                content=row["response"],
                id=row["_id"],
                )
                            
        messages.append(user_message)
        messages.append(assistant_message)

    
    current_convo = Conversation(
        messages=messages,
        chat_id=convo_id,
        created_at=datetime.now(),
    )
        
    all_conversations.append(current_convo)
    count +=1
    if count > sample_size:
        break

# conversation = [
#     Conversation(
#         messages=[
#             Message(
#                 created_at=str(datetime.now()),
#                 role=message["role"],
#                 content=message["content"],
#             )
#             for message in conversation
#         ],
#         id=str(uuid4()),
#         created_at=datetime.now(),
#     )
# ]

kura = Kura(
    embedding_model=OpenAIEmbeddingModel(),
    summarisation_model=SummaryModel(),
    dimensionality_reduction=HDBUMAP(),
    max_clusters=10,
    checkpoint_dir="./checkpoints",
)
# kura.load_conversations("conversations.json")
# run(kura.cluster_conversations())

# conversations: list[Conversation] = Conversation.from_claude_conversation_dump(
#     "conversations.json"
# )
run(kura.cluster_conversations(all_conversations))