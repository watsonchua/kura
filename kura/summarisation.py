from kura.base_classes import BaseSummaryModel
from kura.types import Conversation, ConversationSummary
from kura.types.summarisation import GeneratedSummary
from asyncio import Semaphore
from tqdm.asyncio import tqdm_asyncio
import google.generativeai as genai
import instructor
import os


class SummaryModel(BaseSummaryModel):
    def __init__(
        self,
        max_concurrent_requests: int = 50,
        checkpoint_dir: str = "checkpoints",
        checkpoint_file: str = "summarisation_checkpoint.json",
    ):
        self.sem = Semaphore(max_concurrent_requests)
        self.client = instructor.from_gemini(
            genai.GenerativeModel(
                model_name="gemini-1.5-flash-latest",
            ),
            use_async=True,
        )
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_file = checkpoint_file

        if not os.path.exists(self.checkpoint_dir):
            print(f"Creating checkpoint directory {self.checkpoint_dir}")
            os.makedirs(self.checkpoint_dir)

    def load_checkpoint(self):
        print(
            f"Loading Summary Checkpoint from {os.path.join(self.checkpoint_dir, self.checkpoint_file)}"
        )
        with open(os.path.join(self.checkpoint_dir, self.checkpoint_file), "r") as f:
            return [ConversationSummary.model_validate_json(line) for line in f]

    def save_checkpoint(self, summaries: list[ConversationSummary]):
        with open(os.path.join(self.checkpoint_dir, self.checkpoint_file), "w") as f:
            for summary in summaries:
                f.write(summary.model_dump_json() + "\n")

        print(
            f"Saved {len(summaries)} summaries to {os.path.join(self.checkpoint_dir, self.checkpoint_file)}"
        )

    async def summarise(
        self, conversations: list[Conversation]
    ) -> list[ConversationSummary]:
        if os.path.exists(os.path.join(self.checkpoint_dir, self.checkpoint_file)):
            return self.load_checkpoint()

        summaries = await tqdm_asyncio.gather(
            *[
                self.summarise_conversation(conversation)
                for conversation in conversations
            ],
            desc=f"Summarising {len(conversations)} conversations",
        )

        self.save_checkpoint(summaries)
        return summaries

    async def apply_hooks(
        self, conversation: ConversationSummary
    ) -> ConversationSummary:
        # TODO: Implement hooks here for extra metadata extraction
        return await super().apply_hooks(conversation)

    async def summarise_conversation(
        self, conversation: Conversation
    ) -> ConversationSummary:
        resp = await self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """
                    Generate a summary of the task that the user is asking the language model to do based off the following conversation.


                    The summary should be concise and short. It should be at most 1-2 sentences and at most 30 words. Here are some examples of summaries:
                    - The user’s overall request for the assistant is to help implementing a React component to display a paginated list of users from a database.
                    - The user’s overall request for the assistant is to debug a memory leak in their Python data processing pipeline.
                    - The user’s overall request for the assistant is to design and architect a REST API for a social media application.
                    

                    Here is the conversation
                    <messages>
                    {% for message in messages %}
                        <message>{{message.role}}: {{message.content}} </message>
                    {% endfor %}
                    </messages>

                    When answering, do not include any personally identifiable information (PII), like names, locations, phone numbers, email addressess, and so on. When answering, do not include any proper nouns. Make sure that you're clear, concise and that you get to the point in at most two sentences.
                    
                    For example:

                    Remember that
                    - Summaries should be concise and short. They should each be at most 1-2 sentences and at most 30 words.
                    - Summaries should start with "The user's overall request for the assistant is to"
                    - Make sure to omit any personally identifiable information (PII), like names, locations, phone numbers, email addressess, company names and so on.
                    - Make sure to indicate specific details such as programming languages, frameworks, libraries and so on which are relevant to the task.
                    """,
                }
            ],
            context={"messages": conversation.messages},
            response_model=GeneratedSummary,
        )
        return ConversationSummary(
            chat_id=conversation.chat_id,
            summary=resp.summary,
            metadata={
                "conversation_turns": len(conversation.messages),
            },
        )
