from alerting import app
import os


if __name__ == '__main__':
    app.run(host=app.config['HOST'], port=app.config['PORT'])
