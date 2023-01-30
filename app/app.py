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


class TagSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Tag
        load_instance = True

    content = ma.auto_field()


singular_tag_schema = TagSchema()
plural_tags_schema = TagSchema(many=True)


class CommentSchema(ma.SQLAlchemySchema):

    class Meta:
        model = Comment
        load_instance = True

    author = ma.Nested(single_user_schema)
    timestamp = ma.auto_field()
    content = ma.auto_field()
    id = ma.auto_field()


single_user_schema = UserSchema()
plural_users_schema = UserSchema(many=True)


class PostSchema(ma.SQLAlchemySchema):

    class Meta:
        model = Post
        load_instance = True

    timestamp = ma.auto_field()
    content = ma.auto_field()
    post_type = ma.auto_field()
    selected = ma.auto_field()
    author = ma.Nested(single_user_schema)
    id = ma.auto_field()


single_post_schema = PostSchema()
plural_post_schema = PostSchema(many=True)


class ArticleSchema(ma.SQLAlchemySchema):

    class Meta:
        model = Article
        load_instance = True

    timestamp = ma.auto_field()
    title = ma.auto_field()
    posts = ma.Nested(plural_post_schema)
    id = ma.auto_field()
    # tags = ma.Nested(plural_tags_schema)
    tags = ma.Pluck(TagSchema, 'content', many=True)


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

class UserTokenByUsername(Resource):

    def get(self, username):
        response = AuthClient.get_token(request.headers["authorization"])
        # TODO handle exception

        response = make_response(
            response,
            201,
        )

        return response

api.add_resource(UserTokenByUsername, '/users/<string:username>/token')

class Articles(Resource):
    def get(self):
        return make_response(plural_articles_schema.dump(Article.query.all()))

    @token_required
    def post(self, user_data):
        article = Article(title=request.json['title'])
        db.session.add(article)
        db.session.commit()
        for tag in request.json['tags']:
            new_tag = Tag(content=tag, article_id=article.id)
            db.session.add(new_tag)
            db.session.commit()
        post = Post(post_type="QUESTION", content=request.json['posts'][0]['content'],
                    article_id=article.id, author_id=user_data['id'], selected=False)
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


# TODO post answer, post vote to post, post comment to post, select answer, deselect answer