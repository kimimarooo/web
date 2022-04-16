from flask import Flask, render_template, redirect, request, abort, make_response, jsonify
from data import db_session, activities_resources, users_resources
from data.users import User
from data.activities import Activities
from forms.user import RegisterForm, LoginForm, DetailsForm
from forms.activities import ActivityForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_restful import abort, Api

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
api = Api(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/")
def index():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        activities = db_sess.query(Activities).filter(
            (Activities.user == current_user) | (Activities.is_private != True))
    else:
        activities = db_sess.query(Activities).filter(Activities.is_private != True)
    return render_template("index.html", activities=activities)

@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', form=form)

@app.route("/details", methods=['GET', 'POST'])
def details():
    form = DetailsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        db_sess.commit()
    return render_template('details.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/activities', methods=['GET', 'POST'])
@login_required
def add_activity():
    form = ActivityForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        activities = Activities()
        activities.title = form.title.data
        activities.content = form.content.data
        activities.is_private = form.is_private.data
        current_user.activities.append(activities)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('activities.html', title='Добавление новости',
                           form=form)


@app.route('/activities/<int:id>', methods=['GET'])
@login_required
def view_activity(id):
    form = ActivityForm()
    db_sess = db_session.create_session()
    activities = db_sess.query(Activities).filter(Activities.id == id,
                                      Activities.user == current_user
                                      ).first()
    if activities:
        form.title.data = activities.title
        form.content.data = activities.content
        form.is_private.data = activities.is_private
    else:
        abort(404)
    return render_template('activities.html',
                           title='Редактирование новости',
                           form=form
                           )

api.add_resource(activities_resources.ActivitiesListResource, '/api/activities')
api.add_resource(activities_resources.ActivitiesResource, '/api/activities/<int:activities_id>')
api.add_resource(users_resources.UsersListResource, '/api/users')
api.add_resource(users_resources.UsersResource, '/api/users/<int:user_id>')

def main():
    db_session.global_init("db/users.sqlite")
    app.run(host='0.0.0.0')

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found!!!'}), 404)

if __name__ == '__main__':
    main()

