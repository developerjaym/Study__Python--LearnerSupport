from datetime import datetime, timedelta
from functools import wraps

import jwt
from AuthClient import AuthClient
from flask import abort, request


def get_now():
    return datetime.utcnow().timestamp()

def token_required(f):
    token_cache = {}
    @wraps(f)
    def wrap(*args, **kwargs):
        # if request has no token, abort
        if "authorization" not in request.headers:
            abort(401)
        token = request.headers["authorization"].split(" ")[1]

        # Caching token
        # If we've validated this token before and it's not expired yet
        #  then proceed without calling auth endpoint
        # If we've validated this token before and it's expired
        #  then abort without calling auth endpoint
        if token in token_cache.keys() and token_cache[token]['exp'] > get_now():
            return f(*args, **kwargs, user_data=token_cache[token]['user_data']) 
        elif token in token_cache.keys() and token_cache[token]['exp'] <= get_now():
            abort(403)
        
        if not AuthClient.validate_token(token):
            abort(403)
        user_data = jwt.decode(token, options={"verify_signature": False})
        token_cache[token] = {'exp': user_data['exp'], 'user_data': user_data}
        
        return f(*args, **kwargs, user_data=user_data)
   
    return wrap

def token_validity_cache(f):
    token_dict = {}
    @wraps(f)
    def wrap(*args, **kwargs):
        # if request has no token, abort
        if not request.headers["authorization"]:
            abort(401)
        token = request.headers["authorization"].split(" ")[1]
        if not AuthClient.validate_token(token):
            abort(403)
        user_data = jwt.decode(token, options={"verify_signature": False})
        return f(*args, **kwargs, user_data=user_data)
   
    return wrap