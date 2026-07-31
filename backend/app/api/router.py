from fastapi import APIRouter
from app.schemas.user import UserRegisterSchema, UserLoginSchema
from app.services.auth.registrer import register_user
from app.services.auth.login import login_user
from app.services.auth.logout import logout
from fastapi import Response

auth_router = APIRouter()

try:

    @auth_router.post("/register")
    async def register(user: UserRegisterSchema, response: Response):
        
        return await register_user(user, response=response)
        
        

    @auth_router.post("/login")
    async def login(user: UserLoginSchema, response: Response):
        
        return await login_user(user, response=response)
        

    @auth_router.post("/logout")
    async def _logout(response: Response):

        return logout(response=response)

except Exception as e:
    print(f"Error in auth_router: {str(e)}")