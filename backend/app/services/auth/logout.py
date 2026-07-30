from fastapi import Response
from app.utils.main_utile import return_response
    

def logout(response: Response):

    response.delete_cookie("access_token")

    return return_response(
        status_code=200,
        message="Logout successful"
    )
   