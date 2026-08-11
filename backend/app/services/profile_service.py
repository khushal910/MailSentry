import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.config import settings
from app.db.mongodb import get_database
from app.repositories.google_account_repository import GoogleAccountRepository
from app.utils.email_util import send_reset_otp_email
from app.utils.main_utile import hash_password, verify_password
from app.utils.otp_util import generate_otp, hash_otp, verify_otp
from app.utils.rate_limit_util import check_and_update_rate_limit

logger = logging.getLogger("mailsentry.profile_service")


class ProfileService:
    """
    Production-ready Profile Management service.
    Handles user profile retrieval, username updates, OTP-verified email updates,
    password changes, Google account synchronization, and audit logging.
    """

    def __init__(self, google_repo: GoogleAccountRepository | None = None):
        self.google_repo = google_repo or GoogleAccountRepository()

    def _get_user(
        self, user_id: str, projection: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        db = get_database()
        users_col = db[settings.USER_COLLECTION_NAME]
        query = (
            {"$or": [{"_id": str(user_id)}, {"_id": ObjectId(user_id)}]}
            if ObjectId.is_valid(user_id)
            else {"_id": str(user_id)}
        )
        user = users_col.find_one(query, projection)
        if not user:
            logger.error(
                f"[AUDIT] Profile operation failed — User ID={user_id} not found in database."
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User account no longer exists.",
            )
        return user

    def get_profile(self, user_id: str) -> dict[str, Any]:
        """
        Retrieves user profile details including linked Google account status.
        """
        user = self._get_user(user_id, projection={"password": 0, "email_otp_hash": 0})
        google_acc = self.google_repo.find_by_user_id(user_id)

        created_at_str = None
        if user.get("created_at"):
            ca = user["created_at"]
            created_at_str = ca.isoformat() if isinstance(ca, datetime) else str(ca)

        updated_at_str = None
        if user.get("updated_at"):
            ua = user["updated_at"]
            updated_at_str = ua.isoformat() if isinstance(ua, datetime) else str(ua)

        raw_g_email = google_acc.get("google_email") if google_acc else None
        google_email = (
            str(raw_g_email) if (raw_g_email and isinstance(raw_g_email, str)) else None
        )

        has_rt = (
            google_acc.get("refresh_token") is not None
            and bool(str(google_acc.get("refresh_token")).strip())
        ) if (google_acc and "refresh_token" in google_acc) else bool(google_acc)

        google_connected = bool(
            google_acc and google_acc.get("google_connected", True) and has_rt
        )
        if not google_connected and user.get("google_connected"):
            self.google_repo.update_user_google_connected(
                user_id, False, datetime.now(timezone.utc)
            )

        raw_providers = user.get("providers", ["local"])
        if isinstance(raw_providers, str):
            providers = [raw_providers]
        elif isinstance(raw_providers, list):
            providers = [str(p) for p in raw_providers if isinstance(p, str)]
        else:
            providers = ["local"]

        if not providers:
            providers = ["local"]

        raw_username = user.get("username", "")
        username = (
            str(raw_username)
            if (raw_username and not isinstance(raw_username, (dict, list)))
            else ""
        )

        raw_email = user.get("email", "")
        email = (
            str(raw_email)
            if (raw_email and not isinstance(raw_email, (dict, list)))
            else ""
        )

        return {
            "id": str(user["_id"]),
            "username": username,
            "email": email,
            "role": str(user.get("role", "user")),
            "providers": providers,
            "is_active": bool(user.get("is_active", True)),
            "google_connected": google_connected,
            "google_email": google_email,
            "created_at": created_at_str,
            "updated_at": updated_at_str,
        }

    def update_username(
        self, user_id: str, new_username: str, client_ip: str = "unknown"
    ) -> dict[str, Any]:
        """
        Updates user's username.
        Checks for unchanged values and updates DB with audit logging.
        """
        new_username = new_username.strip()
        user = self._get_user(user_id)
        now = datetime.now(timezone.utc)

        if user.get("username") == new_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No changes detected."
            )

        db = get_database()
        users_col = db[settings.USER_COLLECTION_NAME]

        # Check if username is taken by another user
        existing_username = users_col.find_one(
            {"username": new_username, "_id": {"$ne": user["_id"]}}
        )
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username is already taken.",
            )

        users_col.update_one(
            {"_id": user["_id"]},
            {"$set": {"username": new_username, "updated_at": now}},
        )

        logger.info(
            f"[AUDIT] Action=Username Changed | User ID={user_id} | Timestamp={now.isoformat()} | "
            f"IP={client_ip} | Old Username={user.get('username')} | New Username={new_username}"
        )

        return self.get_profile(user_id)

    async def request_email_change(
        self, user_id: str, new_email: str, client_ip: str = "unknown"
    ) -> dict[str, Any]:
        """
        Initiates OTP-verified email change flow.
        Checks for same email or 409 conflict, generates 6-digit OTP, hashes it,
        stores expiry (5 min), and sends OTP email.
        """
        new_email = new_email.strip().lower()
        user = self._get_user(user_id)
        now = datetime.now(timezone.utc)

        if user.get("email") == new_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No changes detected."
            )

        db = get_database()
        users_col = db[settings.USER_COLLECTION_NAME]

        # Check if email is already taken by another user
        existing_email = users_col.find_one(
            {"email": new_email, "_id": {"$ne": user["_id"]}}
        )
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already in use."
            )

        # Rate limiting check for OTP resend (max 3 per window)
        rate_limit_err = check_and_update_rate_limit(db, f"email_change_{user_id}")
        if rate_limit_err:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many OTP requests. Please wait before requesting another OTP.",
            )

        otp = generate_otp()
        otp_hash = hash_otp(otp)
        expiry = now + timedelta(minutes=5)  # 5-minute expiry requirement

        users_col.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "email_change_pending": new_email,
                    "email_otp_hash": otp_hash,
                    "email_otp_expire_at": expiry,
                    "email_otp_attempts": 0,
                    "updated_at": now,
                }
            },
        )

        # Send OTP email
        try:
            send_reset_otp_email(email=new_email, otp=otp)
        except Exception as mail_err:
            logger.error(
                f"[WARNING] Failed to deliver email change OTP to {new_email}: {mail_err}"
            )

        logger.info(
            f"[AUDIT] Action=Email Change Requested | User ID={user_id} | Timestamp={now.isoformat()} | "
            f"IP={client_ip} | Target Email={new_email}"
        )

        return {
            "message": "OTP sent to your new email address. Please enter the 6-digit code to complete verification.",
            "pending_email": new_email,
            "expires_in_seconds": 300,
        }

    def verify_email_change_otp(
        self, user_id: str, otp: str, client_ip: str = "unknown"
    ) -> dict[str, Any]:
        """
        Verifies 6-digit OTP for pending email change.
        Updates user.email, syncs google_accounts email or flags reconnection, invalidates OTP,
        and returns updated profile.
        """
        user = self._get_user(user_id)
        now = datetime.now(timezone.utc)

        pending_email = user.get("email_change_pending")
        stored_hash = user.get("email_otp_hash")
        expire_at = user.get("email_otp_expire_at")
        attempts = user.get("email_otp_attempts", 0)

        if not pending_email or not stored_hash or not expire_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active email change request found. Please request a new OTP.",
            )

        if expire_at.tzinfo is None:
            expire_at = expire_at.replace(tzinfo=timezone.utc)

        db = get_database()
        users_col = db[settings.USER_COLLECTION_NAME]

        # Check expiry
        if now > expire_at:
            users_col.update_one(
                {"_id": user["_id"]},
                {
                    "$unset": {
                        "email_change_pending": "",
                        "email_otp_hash": "",
                        "email_otp_expire_at": "",
                        "email_otp_attempts": "",
                    }
                },
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired. Please request a new one.",
            )

        # Check attempts lockout
        if attempts >= 5:
            users_col.update_one(
                {"_id": user["_id"]},
                {
                    "$unset": {
                        "email_change_pending": "",
                        "email_otp_hash": "",
                        "email_otp_expire_at": "",
                        "email_otp_attempts": "",
                    }
                },
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many failed attempts. Verification locked. Please request a new OTP.",
            )

        # Verify OTP hash
        if not verify_otp(otp, stored_hash):
            new_attempts = attempts + 1
            if new_attempts >= 5:
                users_col.update_one(
                    {"_id": user["_id"]},
                    {
                        "$unset": {
                            "email_change_pending": "",
                            "email_otp_hash": "",
                            "email_otp_expire_at": "",
                            "email_otp_attempts": "",
                        }
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Too many failed attempts. This OTP has been invalidated. Please request a new one.",
                )
            else:
                users_col.update_one(
                    {"_id": user["_id"]}, {"$inc": {"email_otp_attempts": 1}}
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Incorrect OTP. {5 - new_attempts} attempt(s) remaining.",
                )

        # Valid OTP! Perform updates
        old_email = user.get("email")
        new_email = pending_email

        users_col.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "email": new_email,
                    "updated_at": now,
                },
                "$unset": {
                    "email_change_pending": "",
                    "email_otp_hash": "",
                    "email_otp_expire_at": "",
                    "email_otp_attempts": "",
                },
            },
        )

        logger.info(
            f"[AUDIT] Action=Email Changed | User ID={user_id} | Timestamp={now.isoformat()} | "
            f"IP={client_ip} | Old Email={old_email} | New Email={new_email}"
        )

        # Google Account Synchronization & Disconnection on Email Change
        google_acc = self.google_repo.find_by_user_id(user_id)
        had_google_connected = bool(
            user.get("google_connected")
            or (google_acc and google_acc.get("google_connected"))
        )

        if google_acc or had_google_connected:
            if google_acc:
                self.google_repo.collection.update_one(
                    {"_id": google_acc["_id"]},
                    {
                        "$set": {
                            "google_email": new_email,
                            "google_connected": False,
                            "updated_at": now,
                        }
                    },
                )
            users_col.update_one(
                {"_id": user["_id"]},
                {"$set": {"google_connected": False, "updated_at": now}},
            )
            logger.info(
                f"[AUDIT] Action=Google Account Disconnected On Email Change | User ID={user_id} | "
                f"Timestamp={now.isoformat()} | IP={client_ip}"
            )

        updated_profile = self.get_profile(user_id)
        if had_google_connected:
            updated_profile["notice"] = (
                "Your Google account has been disconnected. Please reconnect your Google account with your new email address."
            )

        return updated_profile

    def change_password(
        self,
        user_id: str,
        current_pw: str,
        new_pw: str,
        confirm_pw: str,
        client_ip: str = "unknown",
    ) -> dict[str, Any]:
        """
        Changes password for local accounts.
        Validates current password, hashes new password with bcrypt, updates DB with audit logging.
        """
        if not current_pw or not current_pw.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is required.",
            )

        if not new_pw or not new_pw.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password is required.",
            )

        if new_pw != confirm_pw:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password and confirm password do not match.",
            )

        if len(new_pw.strip()) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long.",
            )

        user = self._get_user(user_id)
        providers = user.get("providers", ["local"])

        if "local" not in providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google-authenticated accounts cannot change password directly.",
            )

        existing_pw_hash = user.get("password")
        if not existing_pw_hash or not verify_password(current_pw, existing_pw_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect.",
            )

        new_hash = hash_password(new_pw)
        now = datetime.now(timezone.utc)

        db = get_database()
        users_col = db[settings.USER_COLLECTION_NAME]
        users_col.update_one(
            {"_id": user["_id"]}, {"$set": {"password": new_hash, "updated_at": now}}
        )

        logger.info(
            f"[AUDIT] Action=Password Changed | User ID={user_id} | Timestamp={now.isoformat()} | IP={client_ip}"
        )

        return {"message": "Password changed successfully."}
