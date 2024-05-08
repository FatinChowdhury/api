from typing import Annotated

from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends, HTTPException, Path
from starlette import status

import models
from models import Todos
from database import engine, SessionLocal


app = FastAPI()

models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db        # from def get_db() till this line here, code executed before sending response
    finally:
        db.close()      # executed after response delivered

        # makes fastapi faster (fetch info from db, return it to client, close the connection to db after)

db_dependency = Annotated[Session, Depends(get_db)]


class TodoRequest(BaseModel):       # not passing id as request (cuz primary key, want database to increment id, so id is unique)
    title: str
    description: str
    priority: int
    complete: bool


@app.get("/", status_code=status.HTTP_200_OK)
async def read_all(db: db_dependency):
    return db.query(Todos).all()


@app.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(db: db_dependency, todo_id: int = Path(gt=0)):
    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()
    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code = 404, detail = 'Todo not found.')
