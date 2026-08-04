from fastapi import HTTPException, status

from app.core.config import settings
from app.db.mongodb import get_database
from app.schemas.user import ResetPasswordRequest
from app.utils.main_utile import (
    hash_password,
    return_response,
    verify_password_reset_token,
)


async def reset_password_service(payload: ResetPasswordRequest):
    """Handle POST /reset-password.
    Verifies the reset token, hashes the new password, updates the user in the database,
    and removes all OTP fields.
    """
    try:
        # 1. Verify token & purpose (raises HTTPException 401 on invalid/expired/wrong purpose)
        token_payload = verify_password_reset_token(payload.reset_token)
        email = token_payload.get("email")

        if not email:
            return return_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid token payload: email missing",
            )

        db = get_database()
        users_col = db[settings.USER_COLLECTION_NAME]
        user = users_col.find_one({"email": email})

        if not user:
            return return_response(
                status_code=status.HTTP_404_NOT_FOUND, message="User not found"
            )

        # 2. Hash the new password
        hashed_pwd = hash_password(payload.new_password)

        # 3. Update database & remove all OTP fields and forgot password rate limiting timestamps
        users_col.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "password": hashed_pwd,
                },
                "$unset": {
                    "reset_otp_hash": "",
                    "reset_otp_expire_at": "",
                    "reset_otp_attempts": "",
                    "forgot_password_otp_timestamps": "",
                },
            },
        )

        return return_response(
            status_code=status.HTTP_200_OK,
            message="Password has been reset successfully",
        )

    except HTTPException as he:
        # Propagate or handle the JWT signature errors gracefully
        return return_response(status_code=he.status_code, message=he.detail)
    except Exception as e:
        return return_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Error resetting password: {e!s}",
        )
