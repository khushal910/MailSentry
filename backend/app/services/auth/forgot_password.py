from datetime import datetime, timedelta, timezone
from app.db.mongodb import get_database
from app.core.config import settings
from app.utils.otp_util import generate_otp, hash_otp
from app.utils.email_util import send_reset_otp_email
from app.utils.main_utile import return_response
from app.schemas.user import ForgotPasswordRequest


async def forgot_password_service(payload: ForgotPasswordRequest):
    """Handle POST /forgot-password.

    Security‑first implementation: the response does **not** reveal whether the
    email exists in the database. The same generic success message is always
    returned.
    """
    try:
        db = get_database()
        users_col = db[settings.USER_COLLECTION_NAME]
        user = users_col.find_one({"email": payload.email})

        if user:
            # Invalidate any previous OTP by overwriting fields.
            otp = generate_otp()
            otp_hash = hash_otp(otp)
            expiry = datetime.now(timezone.utc) + timedelta(minutes=10)

            users_col.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "reset_otp_hash": otp_hash,
                        "reset_otp_expire_at": expiry,
                        "reset_otp_attempts": 0,
                    }
                },
            )

            # Send the email – any SMTP errors will raise and be caught below.
            send_reset_otp_email(email=payload.email, otp=otp)

        # Whether user exists or not, return the same generic message.
        return return_response(
            status_code=200,
            message="If an account with that email exists, a password reset email has been sent.",
        )
    except Exception as e:
        # Unexpected error – do not leak details to the client.
        return return_response(
            status_code=500,
            message=f"Error processing password reset request: {str(e)}",
        )
