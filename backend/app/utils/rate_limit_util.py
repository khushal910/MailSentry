from datetime import datetime, timezone, timedelta
from pymongo.database import Database
from app.utils.main_utile import return_response

def check_and_update_rate_limit(db: Database, email: str) -> dict | None:
    """
    Checks if the email has exceeded the limit of 3 requests per 15 minutes.
    If exceeded, returns a 429 response dict.
    If not exceeded, records the current timestamp and returns None.
    
    This works for both existent and non-existent users to prevent email enumeration.
    """
    try:
        col = db["otp_rate_limits"]
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=15)
        
        record = col.find_one({"email": email})
        if record:
            timestamps = record.get("timestamps", [])
            # Filter timestamps in the last 15 minutes
            active_timestamps = []
            for ts in timestamps:
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts > cutoff:
                    active_timestamps.append(ts)
            
            if len(active_timestamps) >= 3:
                return return_response(
                    status_code=429,
                    message="Too many OTP requests. Please try again after 15 minutes."
                )
            
            # Append new timestamp and update
            active_timestamps.append(now)
            col.update_one(
                {"email": email},
                {"$set": {"timestamps": active_timestamps}}
            )
        else:
            # Create new record
            col.insert_one({
                "email": email,
                "timestamps": [now]
            })
            
        return None
    except Exception as e:
        # Fallback if DB operation fails
        return return_response(
            status_code=500,
            message=f"Error checking rate limit: {str(e)}"
        )

def clear_rate_limit(db: Database, email: str) -> None:
    """
    Clears the rate limit record for the given email.
    Called upon successful password reset.
    """
    try:
        col = db["otp_rate_limits"]
        col.delete_one({"email": email})
    except Exception:
        pass
