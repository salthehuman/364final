import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_script import Manager, Shell
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, PasswordField, BooleanField, SelectMultipleField, ValidationError
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
import json
import requests

# Imports for login management
from flask_login import LoginManager, login_required, logout_user, login_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash

############################
# Application configurations
############################
app = Flask(__name__)
app.debug = True
app.use_reloader = True
app.config['SECRET_KEY'] = 'hard to guess string from si364'

#################################
## Initiating Post-Gres Databases
#################################
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost/si364hw8"
## Provided:
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


##################
### App setup ####
##################
manager = Manager(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.init_app(app) # set up login manager

##################
## NYT API  KEY ##
##################
NYT_key = '58c51755a97d4f11abf74fb99d3ffb40'



#########################
##### Set up Models #####
#########################

## User-related Models
# Special model for users to log in
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    articles = db.relationship('PersonalArticleCollection', backref='User')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

########################
## Association tables ##
########################

# Set up association Table between list and articles
#on_list = db.Table('on_list',db.Column('item_id',db.Integer, db.ForeignKey('items.id')),db.Column('list_id',db.Integer, db.ForeignKey('lists.id')))


#########################
## Searches + Articles ##
#########################
searches = db.Table('searches', db.Column('term', db.Integer, db.ForeignKey('searchterms.id')), db.Column('results', db.Integer, db.ForeignKey('items.id')))

#########################
## Users   +  Articles ##
#########################

user_collection = db.Table('user_collection', db.Column('user_id', db.Integer, db.ForeignKey('personallists.id')), db.Column('article_id', db.Integer, db.ForeignKey('items.id')))

class ArticleOnList(db.Model):
    __tablename__ = "items"
    id = db.Column(db.Integer, primary_key=True)
    headline = db.Column(db.String(225))
    author = db.Column(db.String(225))
    summary = db.Column(db.String())
    date = db.Column(db.String())

    def __repr__(self):
        return 'Title: {}'.format(self.headline)


class PersonalArticleCollection(db.Model):
    __tablename__ = "personallists"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(225))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    items = db.relationship('ArticleOnList',secondary=user_collection, backref=db.backref('personallists',lazy='dynamic'),lazy='dynamic')

class SearchQuery(db.Model):
    __tablename__ = 'searchterms'
    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(32), unique=True)
    articles = db.relationship('ArticleOnList', secondary='searches', backref=db.backref('searchterms', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        'Search Query: {}'.format(self.term)




########################
##### Set up Forms #####
########################

class RegistrationForm(FlaskForm):
    email = StringField('Email:', validators=[Required(),Length(1,64),Email()])
    username = StringField('Username:',validators=[Required(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,'Usernames must have only letters, numbers, dots or underscores')])
    password = PasswordField('Password:',validators=[Required(),EqualTo('password2',message="Passwords must match")])
    password2 = PasswordField("Confirm Password:",validators=[Required()])
    submit = SubmitField('Register User')

    #Additional checking methods for the form
    def validate_email(self,field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self,field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1,64), Email()])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

class ToSearchForm(FlaskForm):
    term = StringField("What keyword would you like to search?", validators=[Required()])
    submit = SubmitField("Submit")

class DeleteSearchQueryForm(FlaskForm):
    submit = SubmitField('Delete')


################################
####### Helper Functions #######
################################


def nytSearch(q):
    key = NYT_key
    url = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
    data = requests.get(url, params={'api-key':key, 'q':q}).json()
    return data

def get_or_create_article(headline, author, summary, date):
    article = ArticleOnList.query.filter_by(headline=headline).first()
    if article:
        return article
    else:
        article = ArticleOnList(headline=headline, author=author, summary=summary, date=date)
        db.session.add(article)
        db.session.commit()
        return article

def get_or_create_search_query(term):
    lst = SearchQuery.query.filter_by(term=term).first()
    if not lst:
        lst = SearchQuery(term=term)
        search = nytSearch(term)['response']['docs']
        for x in search:
            title = x['headline']['main']
            author = x['byline']['original']
            summary = x['snippet']
            date = x['pub_date']
            final = get_or_create_article(headline=title, author=author, summary=summary, date=date)
            lst.articles.append(final)
        db.session.add(lst)
        db.session.commit()
    return lst

###################################
##### Routes & view functions #####
###################################

## Error handling routes
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

#####################################
## Login-related routes - provided ##
#####################################

@app.route('/login',methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('index'))
        flash('Invalid username or password.')
    return render_template('login.html',form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out')
    return redirect(url_for('index'))

@app.route('/register',methods=["GET","POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,username=form.username.data,password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('You can now log in!')
        return redirect(url_for('login'))
    return render_template('register.html',form=form)

@app.route('/secret')
@login_required
def secret():
    return render_template('secret.html')


# Other Routes
@app.route('/', methods=["GET","POST"])
def index():
    form = ToSearchForm()
    if request.method == "POST":
        term = form.term.data
        query = get_or_create_search_query(term)
        return redirect(url_for("all_lists"))
    return render_template('base.html', form=form)


@app.route('/all_lists',methods=["GET","POST"])
def all_lists():
    form = DeleteSearchQueryForm()
    lsts = SearchQuery.query.all()
    return render_template('all_lists.html',lists=lsts, form=form)


@app.route('/list/<term>',methods=["GET","POST"])
def one_list(term):
    lst = SearchQuery.query.filter_by(term=term).first()
    items = lst.articles.all()
    return render_template('list_tpl.html', items=items,term=term)

@app.route('/article/<headline>',methods=["GET","POST"]) 
def one_article(headline):
    lst = ArticleOnList.query.filter_by(headline=headline).first()
    headline = headline
    date = lst.date
    summary = lst.summary
    author = lst.author
    return render_template('one_article.html', headline=headline, date=date, summary=summary, author=author)


@app.route('/delete/<lst>',methods=["GET","POST"])
def delete_list(lst):
    delete = SearchQuery.query.filter_by(term=lst).first()
    db.session.delete(delete)
    db.session.commit()
    flash("Delete list " + str(lst))
    return redirect(url_for("all_lists"))


if __name__ == '__main__':
    db.create_all()
    app.run(use_reloader=True, debug=True)






