from fastapi import APIRouter
from app.schemas.user import UserRegisterSchema, UserLoginSchema

auth_router = APIRouter()


@auth_router.post("/register")
async def register(user: UserRegisterSchema):
    return user


@auth_router.post("/login")
async def login(user: UserLoginSchema):
    return user