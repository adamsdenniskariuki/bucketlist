from flask_script import Manager, prompt_bool, Shell
from flask_migrate import Migrate, MigrateCommand
from config import db, app
from bucketlists.models import User, BucketListItems, Bucketlist, UserSchema

migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)


@manager.command
def initdb():
    db.create_all()
    print("Initialization complete")


def shell():
    return dict(
        User=User,
        UserSchema=UserSchema
    )


@manager.command
def dropdb():
    if prompt_bool('Are you sure you want to DELETE all your DATA.'):
        db.drop_all()
        print("All data deleted")

manager.add_command('shell', Shell(make_context=shell))

if __name__ == '__main__':
    manager.run()