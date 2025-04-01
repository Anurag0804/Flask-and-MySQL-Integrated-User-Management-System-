from flask_mysqldb import MySQL
from flask_login import UserMixin

mysql = MySQL()

def init_db(app):
    mysql.init_app(app)

class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

    def get_id(self):
        return str(self.id)
