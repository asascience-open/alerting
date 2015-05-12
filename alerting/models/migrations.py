from alerting import app, db
from mongokit import DocumentMigration

# Users
from alerting.models import user
class UserMigration(DocumentMigration):
    # add any migrations here named "allmigration_*"
    def allmigration01__add_timzone_to_users(self):
        self.target = {'timezone':{'$exists': False}}
        self.update = {'$set':{'timezone': 'America/New_York'}}

    def allmigration01__add_admin_to_users(self):
        self.target = {'admin':{'$exists': False}}
        self.update = {'$set':{'admin': False}}

with app.app_context():
    migration = UserMigration(user.User)
    migration.migrate_all(collection=db['users'])
