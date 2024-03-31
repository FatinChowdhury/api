from typing import Optional
from fastapi import FastAPI, Path, Query, HTTPException
from pydantic import Field, BaseModel
from starlette import status

app = FastAPI()


class Book:
    id: int
    title: str
    author: str
    description: str
    rating: int
    published_date: int

    def __init__(self, id: Optional[int], title, author, description, rating, published_date):
        self.id = id
        self.title = title
        self.author = author
        self.description = description
        self.rating = rating
        self.published_date = published_date


class BookRequest(BaseModel):
    id: Optional[int] = Field(title = 'id is not needed')
    title: str = Field(min_length = 3)      # minimum length of 3 characters
    author: str = Field(min_length = 1)
    description: str = Field(min_length = 1, max_length = 100)
    rating: int = Field(gt = 0, lt = 6)
    published_date: int = Field(gt = 1999, lt = 2031)

    class Config:
        json_schema_extra = {
            'example': {
                'title': 'A new book',
                'author': 'Fatin',
                'description': 'A new description of a book',
                'rating': 5,
                'published_date': 2027
            }
        }


BOOKS = [
    Book(1, "Computer Science Pro", "Fatin", "A nice book", 5, 2018),
    Book(2, "fast with fastAPI", "Fatin", "A great book", 5, 2019),
    Book(3, "Master Endpoints", "Fatin", "An awesome book", 5, 2020),
    Book(4, "HP1", "Author 1", "Book Description", 2, 2021),
    Book(5, "HP2", "Author 2", "Book Description", 3, 2022),
    Book(6, "HP3", "Author 3", "Book Description", 1, 2023)
]


@app.get("/books", status_code=status.HTTP_200_OK)
async def read_all_books():
    return BOOKS



@app.get("/books/{book_id}", status_code=status.HTTP_200_OK)
async def read_book(book_id: int = Path(gt = 0)):
    for book in BOOKS:
        if book.id == book_id:
            return book
    raise HTTPException(status_code=404, detail="Item not found")


@app.get("/books/", status_code=status.HTTP_200_OK)
async def read_book_by_rating(book_rating: int = Query(gt=0, lt=6)):
    books_to_return = []
    for book in BOOKS:
        if book.rating == book_rating:
            books_to_return.append(book)
    return books_to_return



@app.get("/books/publish/", status_code=status.HTTP_200_OK)
async def read_book_by_published_date(published_date: int = Query(gt=1999, lt=2031)):
    books_to_return = []
    for book in BOOKS:
        if book.published_date == published_date:
            books_to_return.append(book)
    return books_to_return


@app.post("/create_book", status_code=status.HTTP_201_CREATED)
async def create_book(book_request: BookRequest):
    new_book = Book(**book_request.dict(), id = find_book_id())
    BOOKS.append(new_book)
    return new_book


def find_book_id(book: Book):
    return 1 if len(BOOKS) == 0 else BOOKS[-1].id + 1
    



@app.put("/books/update_book", status_code=status.HTTP_204_NO_CONTENT)
async def update_book(book: BookRequest):
    book_changed = False
    for i in range(len(BOOKS)):
        if BOOKS[i].id == book.id:      # if the book id is found
            BOOKS[i] = book             # update the book
            book_changed = True         # set flag to true
    if not book_changed:
        raise HTTPException(status_code=404, detail="Item not found")


@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int = Path(gt=0)):
    book_changed = False
    for i in range(len(BOOKS)):
        if BOOKS[i].id == book_id:
            BOOKS.pop(i)
            book_changed = True
            break
    if not book_changed:
        raise HTTPException(status_code=404, detail="Item not found")
