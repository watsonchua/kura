import json
from helpers.types import Conversation, Message, ConversationSummary
from typing import List
import instructor
from asyncio import Semaphore


def load_conversations(path: str) -> List[Conversation]:
    """
    This is a function that loads in the conversations from the given path and yields the user's conversations
    """
    with open(path, "r") as f:
        chat_obj = json.load(f)
        return [
            Conversation(
                chat_id=chat["uuid"],
                created_at=chat["created_at"],
                messages=[
                    Message(
                        created_at=message["created_at"],
                        role=message["sender"],
                        content="\n".join(
                            [
                                item["text"]
                                for item in message["content"]
                                if item["type"] == "text"
                            ]
                        ),
                    )
                    for message in chat["chat_messages"]
                ],
            )
            for chat in chat_obj
        ]


async def summarise_conversation(
    client: instructor.AsyncInstructor, sem: Semaphore, conversation: Conversation
) -> dict:
    """
    This is a function that given a user conversation will return a summary of the user request and the task description

    Task Description: The task is to do X
    User Request: The user's overall request for the assistant is to do Y

    """
    async with sem:
        resp = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """Generate a summary of the task that the user is asking and a description of the task that the assistant is trying to complete based off the following conversation.

                    Here are some examples of user requests
                    <examples>
                    - The user’s overall request for the assistant is to help implementing a React component to display a paginated list of users from a database.
                    - The user’s overall request for the assistant is to debug a memory leak in their Python data processing pipeline.
                    - The user’s overall request for the assistant is to design and architect a REST API for a social media application.
                    </examples>

                    Task descriptions should be concise and short. Here are some examples of task descriptions

                    <examples>
                    The task is to help build a frontend component with React and implement database integration
                    The task is to debug performance issues and optimize memory usage in Python code
                    The task is to design and architect a RESTful API following best practices
                    </examples>

                    Here is the conversation
                    {% for message in messages %}
                    <messages>
                    <message>{{message.role}}: {{message.content}} </message>
                    </messages>
                    {% endfor %}

                    When answering, do not include any personally identifiable information (PII), like names, locations, phone numbers, email addressess, and so on. When answering, do not include any proper nouns. Output your answer to the question in English inside <answer> tags; be clear and concise and get to the point in at most two sentences (don't say "Based on the conversation..." and avoid mentioning Claude/the chatbot). For example:

                    Remember that
                    - User requests and task descriptions should be concise and short. They should each be at most 1-2 sentences and at most 20 words.
                    - User requests should start with "The user's overall request for the assistant is to"
                    - Task descriptions should start with "The task is to"
                    - Make sure to omit any personally identifiable information (PII), like names, locations, phone numbers, email addressess, company names and so on.
                    - Make sure to indicate specific details such as programming languages, frameworks, libraries and so on which are relevant to the task. Also mention the specific source of the data if it's relevant to the task. For instance, if the user is asking to perform a calculation, let's talk about the specific source of the data.
                    """,
                }
            ],
            context={"messages": conversation.messages},
            response_model=ConversationSummary,
        )
        return {
            "chat_id": conversation.chat_id,
            "task_description": resp.task_description,
            "user_request": resp.user_request,
            "turns": len(conversation.messages),
        }
