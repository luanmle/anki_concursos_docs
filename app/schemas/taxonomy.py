import uuid

from pydantic import BaseModel


class TopicResponse(BaseModel):
    topic_id: uuid.UUID
    discipline_id: uuid.UUID
    name: str
    parent_id: uuid.UUID | None


class DisciplineResponse(BaseModel):
    discipline_id: uuid.UUID
    name: str
    parent_id: uuid.UUID | None


class DisciplineListResponse(BaseModel):
    items: list[DisciplineResponse]
    total: int


class TopicListResponse(BaseModel):
    discipline: DisciplineResponse
    items: list[TopicResponse]
    total: int
