from uuid import uuid4
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


DATABASE_URL = "postgresql+psycopg://postgres:admin@127.0.0.1:5432/postgres"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    """Базовый класс для всех моделей таблиц БД"""
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))


class TaskORM(Base):
    """Модель для таблицы задачи в Базе Данных"""
    __tablename__ = "tasks"

    title: Mapped[str]
    completed: Mapped[bool] = mapped_column(default=False) # по умолчанию False


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)

def get_db():
    """Функция для создания сессий с БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost:3000',
    ],
    allow_methods=['*'],
    allow_headers=['*'],
    allow_credentials=True,
)

class Task(BaseModel):
    '''Модель задачи'''
    id: str
    title: str
    completed: bool = False

class TaskCreate(BaseModel):
    title: str

class TaskUpdateSchema(BaseModel):
    title: str | None = None
    completed: bool | None = None

class Category(BaseModel):
    '''Модель категории'''
    id: str
    name: str

class CategoryCreate(BaseModel):
    name: str

class CategoryUpdateSchema(BaseModel):
    name: str | None = None


tasks: list[Task] = []
categories: list[Category] = []


@app.get('/tasks', response_model=list[Task])
def get_tasks():
    '''Получить список задач'''
    return tasks


@app.get('/categories', response_model=list[Category])
def get_categories():
    '''Получить список категорий'''
    return categories


@app.post('/tasks', response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate):
    '''Создать новую задачу'''
    for task in tasks:
        if task.title == payload.title:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Задача с таким названием уже существует')
    new_task = Task(id=str(uuid4()), title=payload.title, completed=False)
    tasks.append(new_task)
    return new_task


@app.post('/categories', response_model=Category, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate):
    '''Создать новую категорию'''
    for category in categories:
        if category.name == payload.name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Категория с таким названием уже существует')
    new_category = Category(id=str(uuid4()), name=payload.name)
    categories.append(new_category)
    return new_category


@app.patch('/tasks/{task_id}', status_code=status.HTTP_200_OK)
def update_task(task_id: str, payload: TaskUpdateSchema):
    for task in tasks:
        if task.id == task_id:
            if payload.title:
                task.title = payload.title
            if payload.completed:
                task.completed = payload.completed
            return task


@app.patch('/categories/{category_id}', status_code=status.HTTP_200_OK)
def update_category(category_id: str, payload: CategoryUpdateSchema):
    for category in categories:
        if category.id == category_id:
            category.name = payload.name
            return category
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Category not found')


@app.delete('/tasks/{task_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str):
    for task in tasks:
        if task.id == task_id:
            tasks.remove(task)
            return

@app.delete('/categories/{category_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: str):
    for category in categories:
        if category.id == category_id:
            categories.remove(category)
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Category not found')
        return
