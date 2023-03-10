#!/usr/bin/env python3

from AuthClient import AuthClient, UserDto
from AuthDecorators import token_required
from flask import Flask, Response, abort, jsonify, make_response, request
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_restful import Api, Resource
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models import db, User, Article, Comment, Post, Tag, Vote
import os
import time

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI')
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
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
    img = ma.auto_field()


singular_user_schema = UserSchema()
plural_users_schema = UserSchema(many=True)


class TagSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Tag
        load_instance = True

    content = ma.auto_field()


singular_tag_schema = TagSchema()
plural_tags_schema = TagSchema(many=True)

class VoteSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Vote
        load_instance = True

    up = ma.auto_field()
    author = ma.Nested(singular_user_schema)


singular_vote_schema = VoteSchema()
plural_votes_schema = VoteSchema(many=True)

class CommentSchema(ma.SQLAlchemySchema):

    class Meta:
        model = Comment
        load_instance = True

    author = ma.Nested(singular_user_schema)
    timestamp = ma.auto_field()
    content = ma.auto_field()
    id = ma.auto_field()


singular_comment_schema = CommentSchema()
plural_comments_schema = CommentSchema(many=True)


class PostSchema(ma.SQLAlchemySchema):

    class Meta:
        model = Post
        load_instance = True

    timestamp = ma.auto_field()
    content = ma.auto_field()
    post_type = ma.auto_field(data_key='type')
    selected = ma.auto_field()
    author = ma.Nested(singular_user_schema)
    id = ma.auto_field()
    comments = ma.Nested(plural_comments_schema)
    votes = ma.Nested(plural_votes_schema)

singular_post_schema = PostSchema()
plural_post_schema = PostSchema(many=True)


class ArticleSchema(ma.SQLAlchemySchema):

    class Meta:
        model = Article
        load_instance = True

    timestamp = ma.auto_field()
    title = ma.auto_field()
    posts = ma.Nested(plural_post_schema)
    id = ma.auto_field()
    tags = ma.Pluck(TagSchema, 'content', many=True)


singular_article_schema = ArticleSchema()
plural_articles_schema = ArticleSchema(many=True)


class Users(Resource):
    def post(self):
        exists = db.session.query(User.id).filter_by(username=request.json['username']).first() is not None
        if exists:
            abort(409)
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
        return make_response(singular_user_schema.dump(user), 200,)


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
        return make_response(
            singular_article_schema.dump(article),
            201,
        )


api.add_resource(Articles, "/articles")


class ArticleById(Resource):
    def get(self, id):
        article = Article.query.filter(Article.id == id).one()
        return make_response(singular_article_schema.dump(article), 200, )


api.add_resource(ArticleById, "/articles/<int:id>")

class Answers(Resource):
    @token_required
    def post(self, id, user_data):
        answer = Post(post_type='ANSWER', content=request.json["content"], article_id = id, author_id = user_data['id'], selected = False)
        db.session.add(answer)
        db.session.commit()
        return make_response(singular_post_schema.dump(answer), 201, )


api.add_resource(Answers, "/articles/<int:id>/answers")

class Comments(Resource):
    @token_required
    def post(self, article_id, post_id, user_data):
        #TODO make sure the post belongs to the article
        comment = Comment(content=request.json["content"], post_id = post_id, author_id = user_data['id'])
        db.session.add(comment)
        db.session.commit()
        return make_response(singular_comment_schema.dump(comment), 201, )


api.add_resource(Comments, "/articles/<int:article_id>/posts/<int:post_id>/comments")

class Votes(Resource):
    @token_required
    def post(self, article_id, post_id, user_data):
        previous_vote = Vote.query.filter(Vote.post_id == post_id, Vote.author_id == user_data['id']).one_or_none()
        if previous_vote != None:
            print("We had a vote from this user already for this post")
            db.session.delete(previous_vote)
        #TODO make sure the post belongs to the article
        vote = Vote(post_id = post_id, author_id = user_data['id'], up = request.json["up"])
        db.session.add(vote)
        db.session.commit()
        return make_response(singular_vote_schema.dump(vote), 201, )


api.add_resource(Votes, "/articles/<int:article_id>/posts/<int:post_id>/votes")

class Selections(Resource):
    @token_required
    def post(self, article_id, post_id, user_data):
        article = Article.query.filter(Article.id == article_id).one()
        post = [article_post for article_post in article.posts if article_post.id == post_id][0]

        if post.post_type == 'QUESTION':
            print('this is a question... not an answer')
            abort(400)
        if post.author_id != user_data['id']:
            print('only the author can select an answer')
            abort(403)
        if post.selected:
            print('this post is already selected')
            return make_response('', 204, )
        if True in (article_post.selected for article_post in article.posts):
            print('article already has a selected answer')
            abort(400)

        post.selected = True
        #TODO make sure the post belongs to the article
        db.session.add(post)
        db.session.commit()
        return make_response('', 204, )

    @token_required
    def delete(self, article_id, post_id, user_data):
        article = Article.query.filter(Article.id == article_id).one()
        post = [article_post for article_post in article.posts if article_post.id == post_id][0]

        if post.post_type == 'QUESTION':
            print('this is a question... not an answer')
            abort(400)
        if post.author_id != user_data['id']:
            print('only the author can select an answer')
            abort(403)
        if not post.selected:
            print('this post is not selected')
            return make_response('', 204, )

        post.selected = False
        #TODO make sure the post belongs to the article
        db.session.add(post)
        db.session.commit()
        return make_response('', 204, )

api.add_resource(Selections, "/articles/<int:article_id>/posts/<int:post_id>/selected")

