from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import check_password_hash
from werkzeug.exceptions import HTTPException
from typing import Optional, Union

from config import KEY, DATABASE
from models import db, User

app = Flask(__name__)
app.secret_key = KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE

db.init_app(app)

with app.app_context():
    db.create_all()

# Initialize the LoginManager for handling user authentication
login_manager = LoginManager()
login_manager.init_app(app)

# Set the login view and login message
login_manager.login_view = 'login'
login_manager.login_message = 'Авторизуйтесь для доступу в профіль'


@login_manager.user_loader
def load_user(user_id: str) -> Optional[UserMixin]:
    """
    Callback function for Flask-Login's user_loader decorator.
    Loads and returns a User object from the database based on the provided user_id.
    """
    with app.app_context():
        user = db.session.get(User, int(user_id))
        return user


@app.route('/')
def index() -> str:
    """
    Route handler for the home page.
    """
    return render_template('index.html', title='Flask-Bot')


@app.route('/register')
def register() -> Response:
    """
    Route handler for the registration page.
    Redirects the user to a registration Telegram bot.
    """
    return redirect('https://t.me/test_task_ihor_bot')


@app.route('/login', methods=['GET', 'POST'])
def login() -> Response:
    """
    Route handler for the login page.
    If the user is already authenticated, it redirects to the account page.
    If the request method is POST, it attempts to log in the user based on the provided credentials.
    If the login is successful, it redirects to the account page.
    If the login fails, it flashes an error message and redirects to the index page.
    """
    if current_user.is_authenticated:
        return redirect(url_for('account', username=current_user.username))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember)
            return redirect(url_for('account', username=user.username))
        flash('Невірний email або пароль')
    return redirect(url_for('index'))


@app.route('/account/<username>')
@login_required
def account(username: str) -> Union[str, Response]:
    """
    Route handler for the account page.
    Retrieves the user based on the provided username from the URL parameter.
    If the authenticated user has the same ID as the retrieved user, it renders the account template.
    If the authenticated user does not have access to the page, it flashes an error message and redirects to the index page.
    """
    user = User.query.filter_by(username=username).first_or_404()
    if current_user.id == user.id:
        return render_template('account.html', user=user, title=f'{username}')
    flash('Ви не маєте доступу до цієї сторінки')
    return redirect(url_for('index'))


@app.route('/logout')
@login_required
def logout() -> Response:
    """
    Route handler for the logout page.
    Logs out the current user by calling the `logout_user()` function.
    Redirects the user to the index page after successful logout.
    """
    logout_user()
    return redirect(url_for('index'))


@app.route('/delete/<int:id>')
@login_required
def delete(id: int) -> Response:
    """
    Route handler for the delete page.
    Deletes the user with the given user_id.
    If the user exists, logs out the current user, deletes the user, commits the changes, and flashes a success message.
    If the user does not exist, flashes an error message.
    Redirects the user to the index page after the deletion.
    """
    user = User.query.get(id)
    if user:
        logout_user()
        db.session.delete(user)
        db.session.commit()
        flash('Обліковий запис видалено')
    else:
        flash('Користувача не знайдено')
    return redirect(url_for('index'))


@app.errorhandler(404)
def page_not_found(error: HTTPException) -> str:
    """
    Error handler for the 404 page not found error.
    Renders the 404 error page template.
    """
    return render_template('page404.html', title='Сторінку не знайдено')


def run() -> None:
    """
    Runs the Flask application with debug mode enabled.
    """
    app.run(debug=True)
