from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    auth_system_id = db.Column(db.Integer, unique=True)
    username = db.Column(db.String, unique=True)
    img = db.Column(db.String)
    email = db.Column(db.String)

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    content = db.Column(db.String)

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    post_type = db.Column(db.String)
    content = db.Column(db.String)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    selected = db.Column(db.Boolean)
    comments = db.relationship('Comment', backref='post')

class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'))

class Article(db.Model):
    __tablename__ = 'articles'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    posts = db.relationship('Post', backref='article')
    tags = db.relationship('Tag', backref='article')
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
