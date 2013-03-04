### Setup databases for development and testing
$ mongo
> use admin
> db.addUser('admin', 'adminpassword')
> db.auth('admin', 'adminpassword')
> use larvamap_development
> db.addUser("larvamap","yourpassword")
> use larvamap_testing
> db.addUser("larvamap","yourpassword")
> exit
