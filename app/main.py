from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from starlette.exceptions import HTTPException as StartletteHTTPException
from schemas.post import CreatePost, PostResponse, UpdatePost
from schemas.user import CreateUser, UserResponse, UpdateUser
from typing import Annotated
from models.index import Post, User
from sqlalchemy import select
from sqlalchemy.orm import Session
from configs.database import Base, get_db, engine

Base.metadata.create_all(bind=engine)
app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent

# Mounting files/folders
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/media", StaticFiles(directory=BASE_DIR / "media"), name="media")


templates = Jinja2Templates(directory=BASE_DIR / "templates")

# pages....

# home page


@app.get('/', include_in_schema=False, name="home")
@app.get('/posts', include_in_schema=False, name="posts")
def read_root(request: Request, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(Post))
    posts = result.scalars().all()
    return templates.TemplateResponse(request, "home.html", {"posts": posts, "title": "Home"})


# specific post page
@app.get('/posts/{post_id}', include_in_schema=False)
def post_page(post_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(Post).where(Post.id == post_id))
    post = result.scalars().first()

    if post:
        title = post.title[:50]
        return templates.TemplateResponse(request, "post.html", {"post": post, "title": title})

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail='Post not found')


@app.get("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
def user_posts_page(
    request: Request,
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    result = db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    result = db.execute(select(Post).where(
        Post.user_id == user_id))
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {"posts": posts, "user": user, "title": f"{user.username}'s Posts"},
    )


# apis....

# User related routes


@app.post('/api/users', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: CreateUser, db: Annotated[Session, Depends(get_db)]):

    result = db.execute(select(User).where(User.username == user.username))
    existing_username = result.scalars().first()

    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exist!!")

    result = db.execute(select(User).where(User.email == user.email))
    existing_email = result.scalars().first()

    if existing_email:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exist!!")

    new_user = User(
        username=user.username,
        email=user.email
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.get('/api/users/{user_id}', response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]):

    result = db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if user:
        return user

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found")


@app.get('/api/users/{user_id}/posts', response_model=list[PostResponse], status_code=status.HTTP_200_OK)
def get_user_posts(user_id: int, db: Annotated[Session, Depends(get_db)]):

    result = db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")

    result = db.execute(select(Post).where(Post.user_id == user_id))
    posts = result.scalars().all()

    return posts


@app.patch('/api/users/{user_id}', response_model=UserResponse)
def update_user(user_id: int, user_update: UpdateUser, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")

    if user_update.username is not None and user_update.username != user.username:
        result = db.execute(select(User).where(
            User.username == user_update.username))
        username_exist = result.scalars().first()

        if username_exist:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="username already exist")

    if user_update.email is not None and user_update.email != user.email:
        result = db.execute(select(User).where(
            User.email == user_update.email))
        email_exist = result.scalars().first()

        if email_exist:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="email already exist")

    if user_update.username is not None:
        user.username == user_update.username

    if user_update.email is not None:
        user.email == user_update.email

    if user_update.image_file is not None:
        user.image_file == user_update.image_file

    db.commit()
    db.refresh(user)
    return user


@app.delete('/api/users/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")

    db.delete(user)
    db.commit()


# Post realted routes


# get all posts
@app.get('/api/posts', response_model=list[PostResponse])
def get_posts(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(Post))
    posts = result.scalars().all()

    return posts


# create post
@app.post('/api/posts', response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post: CreatePost, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(User).where(User.id == post.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    new_post = Post(
        title=post.title,
        content=post.content,
        user_id=post.user_id
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post


@app.get('/api/posts/{post_id}', response_model=PostResponse, status_code=status.HTTP_200_OK)
def get_user_posts(post_id: int, db: Annotated[Session, Depends(get_db)]):

    result = db.execute(select(Post).where(Post.id == post_id))
    post = result.scalars().first()

    if post:
        return post

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail="Post not found")


# fully update post route...
@app.put('/api/posts/{post_id}', response_model=PostResponse, status_code=status.HTTP_200_OK)
def update_post_full(post_id: int, post_data: CreatePost, db: Annotated[Session, Depends(get_db)]):

    result = db.execute(select(Post).where(Post.id == post_id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Post not found")

    if post_data.user_id != post.user_id:
        result = db.execute(select(User).where(User.id == post_data.user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    post.title = post_data.title
    post.content = post_data.content
    post.user_id = post_data.user_id

    db.commit()
    db.refresh(post)


# partially update post route...
@app.patch('/api/posts/{post_id}', response_model=PostResponse, status_code=status.HTTP_200_OK)
def update_post_full(post_id: int, post_data: UpdatePost, db: Annotated[Session, Depends(get_db)]):

    result = db.execute(select(Post).where(Post.id == post_id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Post not found")

    update_post = post_data.model_dump(exclude_unset=True)
    for field, value in update_post.items():
        setattr(post, field, value)

    db.commit()
    db.refresh(post)
    return post


@app.delete('/api/posts/{post_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_posts(post_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(Post).where(Post.id == post_id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Post not found")

    db.delete(post)
    db.commit()


@app.exception_handler(StartletteHTTPException)
def general_http_exception_handler(request: Request, exception: StartletteHTTPException):
    message = (
        exception.detail if exception.detail else "An error occurred. Please check your request and try again.")

    if request.url.path.startswith("/api"):
        return JSONResponse(status_code=exception.status_code, content={"detail": message})

    return templates.TemplateResponse(request, "error.html", {
        "status_code": exception.status_code,
        "title": exception.status_code,
        "message": message
    },
        status_code=exception.status_code,

    )


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):

    if request.url.path.startswith("/api"):
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": exception.errors()})

    return templates.TemplateResponse(request, "error.html", {
        "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
        "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
        "message": "Invalid request. Please check your input and try again."
    },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,

    )
