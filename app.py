import uuid
import datetime
from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase
from flask import Flask, request
from flask_mail import Message, Mail

app = Flask(__name__)
mail = Mail(app)

db = SqliteExtDatabase('auth.db')
class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    username = CharField(unique=True)

class AuthCode(BaseModel):
    code = CharField(unique=True)
    user = ForeignKeyField(User, related_name='codes')
    created = DateTimeField(default=datetime.datetime.now)

db.connect()
db.create_tables([User, AuthCode], safe=True)

@app.route('/auth/init', methods=['POST'])
def auth_init():
    email = request.args.get('email', None)
    if email:
        user, created = User.get_or_create(username=email)
        auth = AuthCode.create(code=uuid.uuid4().hex, user=user)

        msg = Message(
            sender="auth@localhost",
            recipients=[auth.user.username],
            subject='Your one-time code',
            body="Your auth code is: %s" % auth.code
        )
        mail.send(msg)

        return 'Auth code sent.'
    return 'You must provide a valid email address.'

@app.route('/auth/token', methods=['POST'])
def auth_token():
    code = request.args.get('code', None)
    if code:
        try:
            auth = AuthCode.get(
                (AuthCode.code == code) &
                (AuthCode.created >= datetime.datetime.now()-datetime.timedelta(minutes=15))
            )
            user = auth.user
            auth.delete_instance()
            return 'Authentication succeeded for %s' % user.username
        except AuthCode.DoesNotExist:
            return 'Could not find a valid auth code.'
    return 'You must provide a valid auth code.'

if __name__ == "__main__":
    app.run()
