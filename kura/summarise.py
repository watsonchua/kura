from asyncio import Semaphore
from tqdm.asyncio import tqdm_asyncio as asyncio
from .types import Conversation, ConversationSummary
from instructor import AsyncInstructor, from_gemini
import google.generativeai as genai
from pydantic import BaseModel, field_validator
import os


class GeneratedSummary(BaseModel):
    task_description: str
    user_request: str

    @field_validator("user_request")
    def validate_user_request_length(cls, v):
        if len(v.split()) > 30:
            raise ValueError(
                f"User request is {len(v.split())} words long. Please condense the user request by removing any unnecessary/less important details while retaining the core request."
            )
        return v


class SummariseBase:
    def __init__(
        self,
        client: AsyncInstructor = from_gemini(
            genai.GenerativeModel("gemini-1.5-flash-latest"), use_async=True
        ),
        max_concurrent_summaries: int = 40,
        checkpoint_dir: str = "checkpoints",
        checkpoint_file_name: str = "summarized_conversations.json",
    ):
        self.sem = Semaphore(max_concurrent_summaries)
        self.client = client
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_file_name = checkpoint_file_name

    def load_checkpoint(self) -> list[ConversationSummary]:
        with open(
            os.path.join(self.checkpoint_dir, self.checkpoint_file_name), "r"
        ) as f:
            return [ConversationSummary.model_validate_json(line) for line in f]

    def save_checkpoint(self, data: list[ConversationSummary]):
        with open(
            os.path.join(self.checkpoint_dir, self.checkpoint_file_name), "w"
        ) as f:
            for item in data:
                f.write(item.model_dump_json() + "\n")

    async def summarise_conversations(
        self, conversations: list[Conversation]
    ) -> list[ConversationSummary]:
        if os.path.exists(os.path.join(self.checkpoint_dir, self.checkpoint_file_name)):
            return self.load_checkpoint()

        coros = [self._summarise(conversation) for conversation in conversations]
        res = await asyncio.gather(*coros, desc="Summarising Conversations")
        self.save_checkpoint(res)
        return res

    async def _summarise(self, conversation: Conversation) -> ConversationSummary:
        async with self.sem:
            resp = await self.client.chat.completions.create(
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
                    - User requests and task descriptions should be concise and short. They should each be at most 1-2 sentences and at most 30 words.
                    - User requests should start with "The user's overall request for the assistant is to"
                    - Task descriptions should start with "The task is to"
                    - Make sure to omit any personally identifiable information (PII), like names, locations, phone numbers, email addressess, company names and so on.
                    - Make sure to indicate specific details such as programming languages, frameworks, libraries and so on which are relevant to the task. Also mention the specific source of the data if it's relevant to the task. For instance, if the user is asking to perform a calculation, let's talk about the specific source of the data.
                    """,
                    }
                ],
                context={"messages": conversation.messages},
                response_model=GeneratedSummary,
            )
        return ConversationSummary(
            chat_id=conversation.chat_id,
            task_description=resp.task_description,
            user_request=resp.user_request,
            metadata={
                "turns": len(conversation.messages),
            },
        )
