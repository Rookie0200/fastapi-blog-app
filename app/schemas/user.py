from pydantic import BaseModel, ConfigDict, Field, EmailStr


class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=80)


class CreateUser(UserBase):
    password: str = Field(min_length=8)


class UpdateUser(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = Field(default=None, max_length=80)
    image_file: str | None = Field(default=None, min_length=1, max_length=200)


class UserPublicResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    image_file: str | None
    image_path: str


class UserPrivateResponse(UserPublicResponse):
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str
