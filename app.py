from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
import bot


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

db.init_app(app)
with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Авторизуйтесь для доступу в профіль'


@login_manager.user_loader
def load_user(user_id):
    with app.app_context():
        user = db.session.get(User, int(user_id))
        return user


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('account', username=current_user.username))

    return render_template('index.html', title='Flask-Bot')


@app.route('/register', methods=['GET', 'POST'])
def register():
    return redirect('https://t.me/test_task_ihor_bot')


@app.route('/login', methods=['GET', 'POST'])
def login():
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
def account(username):
    user = User.query.filter_by(username=username).first_or_404()
    if current_user.id == user.id:
        return render_template('account.html', user=user, title=f'{username}')
    else:
        flash('Ви не маєте доступу до цієї сторінки')
        return redirect(url_for('index'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/delete/<int:id>')
@login_required
def delete(id):
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
def page_not_found(error):
    return render_template('page404.html', title='Сторінку не знайдено')


if __name__ == '__main__':
    bot.run
    app.run(debug=True)
