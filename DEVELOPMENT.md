### Setup databases for development and testing
$ mongo
> use admin
> db.addUser('admin', 'adminpassword')
> db.auth('admin', 'adminpassword')
> use alerting_development
> db.addUser("alerting","yourpassword")
> use alerting_testing
> db.addUser("alerting","yourpassword")
> exit
