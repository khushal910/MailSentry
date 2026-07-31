from fastapi import APIRouter, Depends, Response
from app.schemas.user import UserRegisterSchema, UserLoginSchema, ForgotPasswordRequest, VerifyResetOtpRequest, ResetPasswordRequest
from app.services.auth.registrer import register_user
from app.services.auth.login import login_user
from app.services.auth.logout import logout
from app.services.auth.me import get_me
from app.services.auth.forgot_password import forgot_password_service
from app.services.auth.verify_reset_otp import verify_reset_otp_service
from app.services.auth.reset_password import reset_password_service
from app.dependencies.auth import get_current_user


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


    @auth_router.post("/forgot-password")
    async def forgot_password(request: ForgotPasswordRequest):
        """Public endpoint for initiating password reset.
        Delegates to forgot_password_service and returns its response.
        The request body is validated by Pydantic.
        """
        return await forgot_password_service(request)


    @auth_router.post("/verify-reset-otp")
    async def verify_reset_otp(request: VerifyResetOtpRequest):
        return await verify_reset_otp_service(request)


    @auth_router.post("/reset-password")
    async def reset_password(request: ResetPasswordRequest):
        return await reset_password_service(request)


    @auth_router.get("/me")
    async def me(current_user: dict = Depends(get_current_user)):
        return get_me(current_user)


except Exception as e:
    print(f"Error in auth_router: {str(e)}")