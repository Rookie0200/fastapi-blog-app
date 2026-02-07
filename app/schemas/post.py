from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from schemas.user import UserResponse


class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)


class CreatePost(PostBase):
    user_id: int


class UpdatePost(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, min_length=1)


class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date_posted: datetime
    user_id: int
    author: UserResponse
