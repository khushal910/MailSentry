from datetime import datetime, timezone

from fastapi import status

from app.core.config import settings
from app.db.mongodb import get_database
from app.schemas.user import VerifyResetOtpRequest
from app.utils.main_utile import create_password_reset_token, return_response
from app.utils.otp_util import verify_otp


async def verify_reset_otp_service(payload: VerifyResetOtpRequest):
    """Handle POST /verify-reset-otp.
    Verifies OTP, handles brute force lockout (5 attempts), unsets OTP fields on success/lockout,
    and returns a short-lived reset token on success.
    """
    try:
        db = get_database()
        users_col = db[settings.USER_COLLECTION_NAME]
        user = users_col.find_one({"email": payload.email})

        if not user:
            return return_response(
                status_code=status.HTTP_404_NOT_FOUND, message="User not found"
            )

        # Check if reset OTP fields exist
        stored_hash = user.get("reset_otp_hash")
        expire_at = user.get("reset_otp_expire_at")
        attempts = user.get("reset_otp_attempts", 0)

        if not stored_hash or not expire_at:
            return return_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="No active password reset request found for this email",
            )

        # Check expiry (make sure we compare timezone-aware datetimes)
        if expire_at.tzinfo is None:
            expire_at = expire_at.replace(tzinfo=timezone.utc)

        if datetime.now(timezone.utc) > expire_at:
            # Clean up expired OTP fields
            users_col.update_one(
                {"_id": user["_id"]},
                {
                    "$unset": {
                        "reset_otp_hash": "",
                        "reset_otp_expire_at": "",
                        "reset_otp_attempts": "",
                    }
                },
            )
            return return_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="OTP has expired. Please request a new one.",
            )

        # Lockout check (already locked out before this attempt)
        if attempts >= 5:
            users_col.update_one(
                {"_id": user["_id"]},
                {
                    "$unset": {
                        "reset_otp_hash": "",
                        "reset_otp_expire_at": "",
                        "reset_otp_attempts": "",
                    }
                },
            )
            return return_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Too many failed attempts. Please request a new OTP.",
            )

        # Compare hashes
        if not verify_otp(payload.otp, stored_hash):
            new_attempts = attempts + 1
            if new_attempts >= 5:
                # Invalidate OTP on 5th failure
                users_col.update_one(
                    {"_id": user["_id"]},
                    {
                        "$unset": {
                            "reset_otp_hash": "",
                            "reset_otp_expire_at": "",
                            "reset_otp_attempts": "",
                        }
                    },
                )
                return return_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Too many failed attempts. This OTP has been invalidated. Please request a new one.",
                )
            else:
                users_col.update_one(
                    {"_id": user["_id"]}, {"$inc": {"reset_otp_attempts": 1}}
                )
                return return_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"Invalid OTP. {5 - new_attempts} attempts remaining.",
                )

        # Success - clean up OTP fields and generate password-reset JWT
        users_col.update_one(
            {"_id": user["_id"]},
            {
                "$unset": {
                    "reset_otp_hash": "",
                    "reset_otp_expire_at": "",
                    "reset_otp_attempts": "",
                }
            },
        )

        reset_token = create_password_reset_token(payload.email)
        return return_response(
            status_code=status.HTTP_200_OK,
            message="OTP verified successfully",
            data={"reset_token": reset_token},
        )

    except Exception as e:
        return return_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Error verifying OTP: {e!s}",
        )
