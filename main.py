from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime
from models import get_db, User, Item, Category, UserResponse, ItemResponse, CategoryResponse, UserCreate, ItemCreate, CategoryCreate
from auth import get_password_hash, verify_password, create_access_token, get_current_user, Token

app = FastAPI()

@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token", response_model=Token)
async def login_for_access_token(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/items/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    categories = db.query(Category).filter(Category.id.in_(item.category_ids)).all()
    db_item = Item(name=item.name, description=item.description, owner_id=current_user.id, categories=categories)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return ItemResponse(
        id=db_item.id,
        name=db_item.name,
        description=db_item.description,
        owner=UserResponse(id=current_user.id, username=current_user.username),
        categories=[category.name for category in categories],
        created_at=db_item.created_at
    )

@app.get("/items/", response_model=List[ItemResponse])
async def read_items(db: Session = Depends(get_db)):
    db_items = db.query(Item).all()
    return [ItemResponse(
            id=item.id,
            name=item.name,
            description=item.description,
            owner=UserResponse(id=item.owner.id, username=item.owner.username),
            categories=[category.name for category in item.categories],
            created_at=item.created_at
            ) for item in db_items
        ]

@app.post("/categories/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    db_category = Category(name=category.name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@app.get("/categories/", response_model=List[CategoryResponse])
def read_categories(db: Session = Depends(get_db)):
    db_categories = db.query(Category).all()
    return [db_category for db_category in db_categories]