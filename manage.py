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
    db.session.add(User(name="Adams Kariuki", email="adams@andela.com", password="adams123"))
    db.session.add(Bucketlist(name="bucket 1",
                              created_by=User.query.filter_by(email="adams@andela.com").first().id))
    db.session.add(Bucketlist(name="bucket 2",
                              created_by=User.query.filter_by(email="adams@andela.com").first().id))
    db.session.add(BucketListItems(name="item 1",
                                   bucketlist_id=Bucketlist.query.filter_by(name="bucket 1").first().id))
    db.session.add(BucketListItems(name="item 2",
                                   bucketlist_id=Bucketlist.query.filter_by(name="bucket 1").first().id))
    db.session.commit()
    print('initialized the database.')


@manager.command
def dropdb():
    if prompt_bool("Are you sure you want to lose all your data"):
        db.drop_all()
        print('Deleted the database.')

if __name__ == '__main__':
    manager.run()