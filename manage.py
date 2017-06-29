from flask_script import Manager, prompt_bool
from flask_migrate import Migrate, MigrateCommand
from config import db, app
from bucketlists.models import User, BucketListItems, Bucketlist

migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)


@manager.command
def initdb():
    db.create_all()
    print("Initialization complete")


@manager.command
def dropdb():
    if prompt_bool('Are you sure you want to DELETE all your DATA.'):
        db.drop_all()
        print("All data deleted")

if __name__ == '__main__':
    manager.run()