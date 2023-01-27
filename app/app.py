#!/usr/bin/env python3

from AuthClient import AuthClient, UserDto
from AuthDecorators import token_required
from flask import Flask, Response, abort, jsonify, make_response, request
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_restful import Api, Resource
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models import db, User, Article, Comment, Post, Tag

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

class ArticleSchema(ma.SQLAlchemySchema):

    class Meta:
        model = Article
        load_instance = True

    timestamp = ma.auto_field()
    title = ma.auto_field()
    id = ma.auto_field()


single_article_schema = ArticleSchema()
plural_articles_schema = ArticleSchema(many=True)

class Users(Resource):
    def post(self):
        response = AuthClient.post_account(request.json)
        # TODO handle exception
        new_user = User(
            id=response['id'],
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

api.add_resource(Users, "/users")

class UserById(Resource):
    def get(self, username):
        user = User.query.filter_by(username=username).first()
        return make_response(single_user_schema.dump(user), 200,)

api.add_resource(UserById, "/users/<string:username>")


class Articles(Resource):
    @token_required
    def post(self, user_data):
        article = Article(title=request.json['title'])
        db.session.add(article)
        db.session.commit()
        for tag in request.json['tags']:
            new_tag = Tag(content = tag, article_id=article.id)
            db.session.add(new_tag)
            db.session.commit()
        post = Post(post_type="QUESTION", content=request.json['posts'][0]['content'], article_id=article.id, author_id = user_data['id'], selected=False)
        db.session.add(post)
        db.session.commit()

        print()
        return make_response(
            single_article_schema.dump(article),
            201,
        )

api.add_resource(Articles, "/articles")

class ArticleById(Resource):
    def get(self, id):
        article = Article.query.filter(Article.id == id).one()
        return make_response(single_article_schema.dump(article), 200, )

api.add_resource(ArticleById, "/articles/<int:id>")