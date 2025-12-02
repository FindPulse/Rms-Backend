from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["Auth"])

class User(BaseModel):
    email: str
    password: str

@router.post("/signup")
def signup(user: User):
    # TODO: add Supabase or DB signup logic
    return {"message": f"User {user.email} registered"}

@router.post("/login")
def login(user: User):
    # TODO: add Supabase or DB login logic
    return {"message": f"User {user.email} logged in"}
