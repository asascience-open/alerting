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
