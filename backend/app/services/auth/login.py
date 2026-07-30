from fastapi import Response

from app.db.mongodb import get_database
from app.utils.main_utile import (
    verify_password,
    create_access_token,
    return_response
)
from app.schemas.user import UserLoginSchema
from app.core.config import settings 
    
async def login_user(user: UserLoginSchema, response: Response):

    db = get_database()
    user_col = db[settings.USER_COLLECTION_NAME]
    db_user = user_col.find_one(
        {"email": user.email}
    )

    if not db_user:
        return return_response(
            status_code=401,
            message="Invalid email or password"
        )

    if not verify_password(user.password, db_user["password"]):
        return return_response(
            status_code=401,
            message="Invalid email or password"
        )

    access_token = create_access_token(
        user_id = str(db_user["_id"]),
        username = db_user["username"]
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.SECURE_COOKIES,      
        samesite="lax",
        max_age=60 * 30
    )

    return return_response(
        status_code=200,
        message="Login successful"
    )