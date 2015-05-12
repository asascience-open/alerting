# alerting
Alerting system for observation assets and forecasting models

## Installation

1. Create a python virtual environment for this project. We recommend [virtualenvburrito](https://github.com/brainsik/virtualenv-burrito)
2. Install the project dependencies
   ```
   pip install -r requirements.txt
   ```
3. Configure the project
   
   In config.yml fill out the following fields with the production values:

   - WEB_PASSWORD
   - SECRET_KEY (should be a secure hash generated at random)
   - MAIL_USERNAME
   - MAIL_PASSWORD
   - MAIL_SENDER

   Also fill out any MongoDB or Redis host information if it's not running on localhost.

4. Install MongoDB

5. Clone the production database:

   1. On Production
      
      ```
      cd /tmp
      mongodump -d alerting_production -o alerting_production
      tar -jcvf alerting_production.tar.bz2
      ```

   2. Copy over the database
      ```
      scp <production>:/tmp/alerting_production.tar.bz2 /tmp/
      ```

   3. Extract and install the production database to the development environment
      ```
      tar -jxvf alerting_production
      mongorestore alerting_production
      ```

6. Elect an administrative user account, for example:

   ```
   mongo alerting_production # Launches the mongo terminal
   > db.users.update({email: 'lcampbell@asascience.com'}, {$set: {admin: true}})
   ```

7. Set up supervisor or some process management/daemon system to launch the web server and worker(s)

8. Use gunicorn to launch the web server on Production, example: (This really should be managed by supervisord)

   ```
   gunicorn -w 2 -b 0.0.0.0:8080 app:app
   ```

9. Launch the worker(s) which will actually run the tasks and do scheduled tasks.

   ```
   python worker.py
   ```

10. Log in as the administrator and visit /jobs

11. Log in as the administrator and visit /regulate
