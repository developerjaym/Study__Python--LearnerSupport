#!/usr/bin/env python3

from AuthClient import AuthClient, UserDto
from AuthDecorators import token_required
from flask import Flask, Response, abort, jsonify, make_response, request
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_restful import Api, Resource
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models import db, User
# from models import (AppInstallation, Chatter, Conversation, Game,
                    # InstallableApp, Message, db)

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
# we need this for some reason
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False


migrate = Migrate(app, db)

db.init_app(app)  # do not forget this line !!!
api = Api(app)

ma = Marshmallow(app)  # be sure this line comes after the db stuff

class UserSchema(ma.SQLAlchemySchema):

    class Meta:
        model = User
        load_instance = True

    username = ma.auto_field()
    email = ma.auto_field()
    img = ma.auto_field()
    id = ma.auto_field()


single_user_schema = UserSchema()
plural_users_schema = UserSchema(many=True)


class CreateUser(Resource):
    def post(self):
        response = AuthClient.post_account(request.json)
        # TODO handle exception
        new_user = User(
            auth_system_id=response['id'],
            username=request.json['username'],
            email=request.json['email'],
            img=request.json.get('img', None)
        )
        db.session.add(new_user)
        db.session.commit()

        response = make_response(
            response,
            201,
        )

        return response

api.add_resource(CreateUser, "/users")

class UserById(Resource):
    def get(self, username):
        user = User.query.filter_by(username=username).first()
        return make_response(single_user_schema.dump(user), 200,)

api.add_resource(UserById, "/users/<string:username>")
