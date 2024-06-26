from typing import Annotated

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends, HTTPException, Path
from starlette import status

import models
from models import Todos
from database import engine, SessionLocal
from routers import auth, todos

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(todos.router)

def get_db():
    db = SessionLocal()
    try:
        yield db        # from def get_db() till this line here, code executed before sending response
    finally:
        db.close()      # executed after response delivered

        # makes fastapi faster (fetch info from db, return it to client, close the connection to db after)

db_dependency = Annotated[Session, Depends(get_db)]


class TodoRequest(BaseModel):       # not passing id as request (cuz primary key, want database to increment id, so id is unique)
    title: str  = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
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

@app.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(db: db_dependency, todo_request: TodoRequest):
    todo_model = Todos(**todo_request.dict())
    db.add(todo_model) 
    db.commit()     # from here, u can change in Create todo of website, id will be ++

@app.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(db: db_dependency, todo_request: TodoRequest, todo_id: int = Path(gt=0)):
    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete
    # use same todo model that we're retrieving from the database
    # because SQLalchemy will know that this is the todo
    # (above if statement) within the database record that we are changing
    # when we submit a new todo

    # if we create a new todo and then submit it, SQLalchemy thinks we are creating
    # a new object of a todo and trying to save it within database where
    # a) it needs to autoincrement the ID
    # b) it needs to update the existing todo record
    # one of these will throw error, other will create duplicate of record

    db.add(todo_model)
    db.commit()

''' from here, open browser and go to read all (all four of todos are saved in db)
take third todo, copy it, scroll down (till u see put request, so Update Todo)
paste the body of the Todo in update todo, id is 3, so enter 3 as todo_id
remove the id from the request
make priority 1, set complete to true
then u should get 204 response (HTTP success with no content) 
go back to read all and you will see it being updated
'''
@app.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: db_dependency, todo_id: int = Path(gt=0)):
    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    db.query(Todos).filter(Todos.id == todo_id).delete()

    db.commit()
