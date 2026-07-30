from fastapi import Request
from app.db.mongodb import get_database
from app.utils.main_utile import decode_token, return_response
from bson import ObjectId

async def get_current_user(request: Request):
    
    token = request.cookies.get("access_token")
    if not token:
        return return_response(
            status_code=401,
            message="Authentication required"
        )

    payload = decode_token(token)

    db = get_database()
    user = await db.find_one(
        {"_id": ObjectId(payload["user_id"])},
    )

    if user is None:
        return return_response(
            status_code=401,
            message="User not found"
        )

    request.state.user = user