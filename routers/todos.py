# cleaning up application for scalability and maintainability

from typing import Annotated

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path
from starlette import status
from models import Todos
from database import SessionLocal
from .auth import get_current_user

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db        # from def get_db() till this line here, code executed before sending response
    finally:
        db.close()      # executed after response delivered

        # makes fastapi faster (fetch info from db, return it to client, close the connection to db after)

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


class TodoRequest(BaseModel):       # not passing id as request (cuz primary key, want database to increment id, so id is unique)
    title: str  = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    complete: bool


@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    return db.query(Todos).filter(Todos.owner_id == user.get('id')).all()


@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()
    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code = 404, detail = 'Todo not found.')
    # run uvicorn

@router.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequest):
    
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    todo_model = Todos(**todo_request.dict(), owner_id=user.get('id')) # now do uvicorn
    
    db.add(todo_model)  
    db.commit()     # from here, u can change in Create todo of website, id will be ++

@router.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequest, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    # now u can update request based on authentication
    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()
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
@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')

    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).delete()
    db.commit()
    
