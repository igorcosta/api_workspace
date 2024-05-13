from fastapi import APIRouter, HTTPException, status
from typing import List
from models import User, Task, Profile, Workspace, Work
from schemas import UserCreate, TaskCreate, ProfileCreate, WorkspaceCreate, WorkCreate, WorkUpdate
from database import get_db
from sqlalchemy.orm import Session
from fastapi.params import Depends

router = APIRouter()

@router.post("/users/", response_model=UserCreate, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/users/", response_model=List[UserCreate])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.put("/users/{user_id}", response_model=UserCreate)
def update_user(user_id: int, user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    for var, value in vars(user).items():
        setattr(db_user, var, value) if value else None
    db.commit()
    return db_user

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return {"ok": True}

# Work endpoints
@router.post("/works", response_model=WorkCreate, status_code=status.HTTP_201_CREATED)
def create_work(work: WorkCreate, db: Session = Depends(get_db)):
    db_work = Work(**work.dict())
    db.add(db_work)
    db.commit()
    db.refresh(db_work)
    return db_work

@router.get("/works/{work_id}", response_model=WorkCreate)
def get_work(work_id: int, db: Session = Depends(get_db)):
    db_work = db.query(Work).filter(Work.id == work_id).first()
    if db_work is None:
        raise HTTPException(status_code=404, detail="Work not found")
    return db_work

@router.put("/works/{work_id}", response_model=WorkUpdate)
def update_work(work_id: int, work: WorkUpdate, db: Session = Depends(get_db)):
    db_work = db.query(Work).filter(Work.id == work_id).first()
    if db_work is None:
        raise HTTPException(status_code=404, detail="Work not found")
    for var, value in vars(work).items():
        setattr(db_work, var, value) if value else None
    db.commit()
    return db_work

@router.delete("/works/{work_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work(work_id: int, db: Session = Depends(get_db)):
    db_work = db.query(Work).filter(Work.id == work_id).first()
    if db_work is None:
        raise HTTPException(status_code=404, detail="Work not found")
    db.delete(db_work)
    db.commit()
    return {"ok": True}
