from fastapi import Response

from app.utils.main_utile import return_response


def logout(response: Response):
    """This function handles user logout by deleting the access token cookie."""

    try:
        response.delete_cookie("access_token")

        return return_response(status_code=200, message="Logout successful")
    except Exception as e:
        return return_response(
            status_code=500, message=f"Error during logout: {e!s}"
        )
