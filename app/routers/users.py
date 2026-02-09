from fastapi import APIRouter, HTTPException, status, Depends
from schemas.post import PostResponse
from schemas.user import CreateUser, UserPrivateResponse, UserPublicResponse, UpdateUser, Token
from typing import Annotated
from models.index import Post, User
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from core.database import get_db
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from services.auth import create_access_token, hash_password, verify_access_token, verify_password, oauth2_scheme
from core.config import settings
from services.auth import CurrentUser


router = APIRouter()


@router.post('', response_model=UserPrivateResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: CreateUser, db: Annotated[AsyncSession, Depends(get_db)]):

    result = await db.execute(select(User).where(func.lower(User.username) == user.username.lower()))
    existing_username = result.scalars().first()

    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exist!!")

    result = await db.execute(select(User).where(func.lower(User.email) == user.email.lower()))
    existing_email = result.scalars().first()

    if existing_email:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exist!!")

    new_user = User(
        username=user.username,
        email=user.email.lower(),
        password_hash=hash_password(user.password)
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post('/token', response_model=Token)
async def access_token_for_login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(User).where(func.lower(User.email) == form_data.username.lower()))
    user = result.scalars().first()

    if not user and not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})

    access_token_expires = timedelta(
        minutes=settings.access_token_expire_minutes)

    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires)

    return Token(access_token=access_token, token_type="bearer")


@router.get('/me', response_model=UserPrivateResponse)
async def get_current_user(current_user: CurrentUser):
    return current_user


@router.get('/{user_id}', response_model=UserPublicResponse, status_code=status.HTTP_200_OK)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if user:
        return user

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found")


@router.get('/{user_id}/posts', response_model=list[PostResponse], status_code=status.HTTP_200_OK)
async def get_user_posts(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")

    result = await db.execute(select(Post).options(selectinload(Post.author)).where(Post.user_id == user_id).order_by(Post.date_posted.desc()))
    posts = result.scalars().all()

    return posts


@router.patch('/{user_id}', response_model=UserPrivateResponse)
async def update_user(user_id: int, user_update: UpdateUser, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")

    if user_update.username is not None and user_update.username.lower() != user.username.lower():
        result = await db.execute(select(User).where(func.lower(
            User.username) == user_update.username.lower()))
        username_exist = result.scalars().first()

        if username_exist:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="username already exist")

    if user_update.email is not None and user_update.email.lower() != user.email.lower():
        result = await db.execute(select(User).where(func.lower(
            User.email) == user_update.email.lower()))
        email_exist = result.scalars().first()

        if email_exist:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="email already exist")

    if user_update.username is not None:
        user.username = user_update.username

    if user_update.email is not None:
        user.email = user_update.email.lower()

    if user_update.image_file is not None:
        user.image_file = user_update.image_file

    await db.commit()
    await db.refresh(user)
    return user


@router.delete('/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")

    await db.delete(user)
    await db.commit()
