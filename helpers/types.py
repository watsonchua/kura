from pydantic import BaseModel, field_validator, computed_field, Field, ValidationInfo
import uuid


class Message(BaseModel):
    created_at: str
    role: str
    content: str


class Conversation(BaseModel):
    chat_id: str
    created_at: str
    messages: list[Message]


class Cluster(BaseModel):
    id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
    )
    name: str
    description: str
    parent_id: str | None
    chat_ids: list[str]

    @computed_field
    def count(self) -> int:
        return len(self.chat_ids)

    def add_child_count(self, child: "Cluster"):
        return Cluster(
            name=self.name,
            description=self.description,
            chat_ids=self.chat_ids + child.chat_ids,
        )


class ConversationSummary(BaseModel):
    task_description: str
    user_request: str

    @field_validator("user_request", "task_description")
    def validate_length(cls, v):
        if len(v.split()) > 25:
            raise ValueError(
                f"Please summarize the sentence {v} to at most 20 words. It's currently {len(v.split())} words long. Remove any unnecessary words and make sure to retain the most important information."
            )
        return v


class ClusterSummary(BaseModel):
    """
    This is a summary of the related statements into a single cluster that captures the essence of these statements and distinguishes them from the contrastive answers of other groups.

    Your job is to create a final name and summary for the cluster
    """

    name: str
    summary: str


class CandidateClusters(BaseModel):
    candidate_cluster_names: list[str]

    @field_validator("candidate_cluster_names")
    def validate_length(cls, v, info: ValidationInfo):
        desired_number = info.context["desired_number"]
        if len(v) > desired_number:
            raise ValueError(
                f"Too many candidate cluster names: got {len(v)}, expected at most {desired_number}. Please combine similar clusters to reduce the total number."
            )
        return v


class ClusterLabel(BaseModel):
    higher_level_cluster: str

    @field_validator("higher_level_cluster")
    def validate_length(cls, v, info: ValidationInfo):
        candidate_clusters = info.context["candidate_clusters"]
        if v not in candidate_clusters:
            raise ValueError(
                f"The chosen label of {v} is not in the list of candidate clusters provided of {candidate_clusters}. You must choose a label that belongs to the list of candidate clusters - {candidate_clusters}."
            )
        return v


class ConsolidatedCluster(BaseModel):
    """
    This is a consolidated cluster that is the result of merging multiple clusters into a single higher levle cluster
    """

    cluster_name: str
    cluster_description: str
