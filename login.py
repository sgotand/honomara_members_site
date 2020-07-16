from flask_login import LoginManager, UserMixin, login_user
from honomara_members_site import app
from collections import defaultdict
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return users.get(int(user_id))


class User(UserMixin):
    def __init__(self, id, name, password):
        self.id = id
        self.name = name
        self.password = password


users = {
    1: User(1, "honomara", b'$2b$12$BwaQvntTYqCydE4YBsXCyu2qGNYFoG3lryjSvWUb5oUzAK.5iEI4u'),
    2: User(2, "admin", b'$2b$12$s4YcIkVodAk65E8Tdm6Tsu8aymojDadlBgIg0wx0eJakefO.SF5S2')
}


def nested_dict(): return defaultdict(nested_dict)


user_check = nested_dict()
for i in users.values():
    user_check[i.name]["password"] = i.password
    user_check[i.name]["id"] = i.id


def login_check(username, password):
    if (username in user_check and
            bcrypt.check_password_hash(user_check[username]["password"], password)):
        login_user(users.get(user_check[username]["id"]))
        return True
    else:
        return False
