import uuid

from flask import request, url_for, render_template, redirect, session, flash
from flask.ext.login import login_user, logout_user, current_user

from alerting import db, app, facebook, google, queue
from json import loads
from werkzeug import url_encode
from urllib2 import Request, urlopen, URLError
from alerting.utils import jsonify, nocache
from alerting.tasks.send_email import send


@app.route('/logout')
@nocache
def logout():
    session.pop('facebook_token', None)
    session.pop('google_token', None)
    logout_user()
    flash('Signed out')
    return redirect(request.referrer or url_for('index'))

# FACEBOOK
@app.route('/login_facebook')
@nocache
def login_facebook():
    return facebook.authorize(callback=url_for('facebook_authorized',
                              next=request.args.get('next') or request.referrer or None,
                              _external=True))

@app.route('/login/facebook_authorized')
@facebook.authorized_handler
@nocache
def facebook_authorized(resp):
    if resp is None:
        flash('Access denied')
        return redirect(url_for('index'))

    session['facebook_token'] = (resp['access_token'], '')
    #request 'me' to get user id and email
    me = facebook.get('/me')

    email = unicode(me.data['email'])
    user = db.User.find_one({ 'email' : email })
    if user is None:
        user = register_user(email, password=None, confirmed=True)
    else:
        if not user.confirmed:
            user.confirmed = True
            user.save()
    
    login_user(user)

    if user.password is None:
        next_url = url_for('set_password')
    else:
        next_url = request.args.get('next') or url_for('index')
    return redirect(next_url)

@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('facebook_token')

#GOOGLE
@app.route('/login_google')
@nocache
def login_google():
    return google.authorize(callback=url_for('google_authorized',_external=True))

@app.route('/login/google_authorized')
@google.authorized_handler
@nocache
def google_authorized(resp):
    if resp is None:
        flash('Access denied')
        return redirect(url_for('index'))

    session['google_token'] = (resp['access_token'], '')
    body = {'access_token': resp['access_token']}

    headers = { 'Authorization': 'OAuth ' + resp['access_token'] }
    req = Request('https://www.googleapis.com/oauth2/v1/userinfo', None, headers)

    try:
        res = urlopen(req)

        email = unicode(loads(res.read()).get(u'email'))
        user = db.User.find_one({ 'email' : email })
        if user is None:
            user = register_user(email, password=None, confirmed=True)
        else:
            if not user.confirmed:
                user.confirmed = True
                user.save()

        login_user(user)

        if user.password is None:
            next_url = url_for('set_password')
        else:
            next_url = request.referrer or url_for('index')
        return redirect(next_url)

    except URLError, e:
        if e.code == 401:
            # Unauthorized - bad token
            session.pop('google_token', None)
            flash('Unauthoirzed')
            return redirect(url_for('index'))

@app.route("/set_password", methods=["GET"])
def set_password():
    if current_user.is_active():
        return render_template('set_password.html')
    else:
        return redirect(url_for('index'))

@app.route("/save_password", methods=["POST"])
def save_password():
    if current_user.is_active():
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        if len(password) < 5:
            flash("Password must be at least 5 characters")
            return redirect(url_for('set_password'))

        if password == confirm:
            current_user.password = current_user.generate_password(password)
            current_user.save()
            flash("New password set")
            return redirect(url_for('index'))
        else:
            flash("Passwords do not match")
            return redirect(url_for('set_password'))
    else:
        return redirect(url_for('index'))

@app.route("/signup", methods=["POST"])
def signup():
    email = request.form.get("email")
    user = db.User.find_one({ 'email' : unicode(email) })

    # User already exists
    if user is not None and user.confirmed:
        flash("'%s' already has an account. Try logging in below. " % email )
        return redirect(url_for('index'))
    
    if user is not None and not user.confirmed:
        send_confirmation(user)
        flash("Account created.  Please check your email for instructions")
        return redirect(url_for('index'))

    # Create user
    user = register_user(email, password=None, confirmed=False)
    if user is False:
        flash("Please enter a valid email address")
        return redirect(url_for('index'))
    else:
        send_confirmation(user)
        flash("Account created.  Please check your email for instructions")
        return redirect(url_for('index'))

@app.route("/login_local", methods=["POST"])
def login_local():
    email = request.form.get("email",'')
    password = request.form.get("password",'')

    if email == '' or password == '':
        flash("Invalid login")
        return redirect(url_for('index'))

    user = db.User.find_one({ 'email' : unicode(email) })

    if user is not None:
        # Login
        pass_check = user.check_password(password)
        if pass_check:
            login_user(user)
            flash("Signed in as '%s'" % email)
        elif not user.is_active():
            flash("Email address must be confirmed before logging in.  Check your email for instructions.")
        else:
            flash("Incorrect password for '%s'" % email)
    else:
        flash("No account found for email address '%s'" % email)

    return redirect(url_for('index'))

@app.route('/confirm/<ObjectId:user_id>/<string:confirmation_token>', methods=['GET'])
def confirm_user(user_id, confirmation_token):
    user = db.User.find_one({ '_id' : user_id, 'confirmation_token' : unicode(confirmation_token) })
    if user is not None:
        user.confirmed = True
        user.save()
        login_user(user)
        flash("'%s' has been confirmed" % user.email)
        return redirect(url_for('set_password'))
    else:
        flash("There was an error when trying to confirm your account")
        return redirect(url_for('index'))

def send_confirmation(user):
    queue.enqueue(send,
            subject="[GLOS Alerts] Please confirm your email address",
            sender=app.config.get("MAIL_SENDER"),
            recipients=[user.email],
            text_body=render_template("confirmation_email.txt", 
                user=user),
            html_body=render_template("confirmation_email.html", 
                user=user))

def register_user(email, password=None, confirmed=False):
    user = db.User()
    user.email = email

    if password is not None:
        password = user.generate_password(password)
    user.password = password

    user.confirmed = confirmed
    if confirmed is False:
        user.confirmation_token = user.generate_confirmation_key()

    try:
        user.validate()
        user.save()
        return user
    except:
        return False