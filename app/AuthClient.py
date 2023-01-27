from typing import TypedDict
import requests
import json
from flask import abort
class UserDto(TypedDict):
    username: str
    email: str
    id: int

class AuthClient:
    def post_account(new_account_json):
        URL = "https://jayman.pythonanywhere.com/account"
        response = requests.post(URL, json=new_account_json)
        if response.ok:
            decoded = response.content.decode('utf-8')
            return json.loads(decoded)
        abort(response.status_code)   
    def validate_token(token):
        URL = "https://jayman.pythonanywhere.com/jwt/validate"
        response = requests.get(URL, headers={"Authorization": f"Bearer {token}"})
        if response.ok:
            return True
        return False
    def get_token(basic_auth):
        URL = "https://jayman.pythonanywhere.com/jwt"
        response = requests.get(URL, headers={"Authorization": basic_auth})
        if response.ok:
            decoded = response.content.decode('utf-8')
            return json.loads(decoded)
        abort(response.status_code)     