import uuid
import pytz

from flask import request, url_for, render_template, redirect, session, flash, jsonify
from flask.ext.login import login_user, logout_user, current_user

from alerting import db, app, queue
from json import loads
from werkzeug import url_encode
from urllib2 import Request, urlopen, URLError
from alerting.utils import jsonify, nocache
from alerting.tasks.send_email import send


@app.route('/logout')
@nocache
def logout():
    logout_user()
    flash('Signed out')
    return redirect(request.referrer or url_for('index'))

@app.route("/set_password", methods=["GET"])
def set_password():
    if current_user.is_active():
        return render_template('set_password.html')
    else:
        return redirect(url_for('index'))

@app.route("/forgot_password", methods=['GET','POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('forgot_password.html')
    else:
        email = request.form.get("email", None)
        user = db.User.find_one( { 'email' : email } )
        if user is not None:
            send_confirmation(user)
            flash("Email address '%s' must be confirmed before changing your password.  Check your email for instructions." % email)
            return redirect(url_for('index'))
        else:
            flash("Email address '%s' does not exists in system.  Please create an account." % email)
            return redirect(url_for('forgot_password'))

@app.route("/save_timezone", methods=["POST"])
def save_timezone():
    if current_user and current_user.is_active():
        timezone = unicode(request.form.get("timezone")).strip()
        if timezone in pytz.country_timezones("US"):
            current_user.timezone = timezone
            current_user.save()
            return jsonify({ 'message' : 'Timezone updated.' })
        else:
            return jsonify({ 'message' : 'Unrecognized timezone, please try again.' })
    else:
        return jsonify({ 'message' : 'Error updating timezone, please try again.' })


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

@app.route("/login_local", methods=["POST"])
def login_local():

    user  = None
    email = request.form.get("email", None)
    if email is None:
        flash("Please enter an email address")
        return redirect(url_for('index'))
    else:
        user = db.User.find_one({ 'email' : unicode(email) })

    # New account
    newuser  = request.form.get("iamanewuser",)
    password = request.form.get("password",'')

    if newuser == "true":
        if user is not None:
            # User already exists in the system
            if user.password is not None:
                # Local account already exists in the system
                flash("Account for '%s' already exists, please enter your password." % email)
            else:
                # Email address exists, but no password is set.  They logged in socially and now want to create a local account.
                # Confirm email address
                send_confirmation(user)
                flash("Account created for '%s'.  Please check your email for instructions on confirming your email address." % email)
        else:
            # Create account
            user = register_user(email, password, False)
            if user is not False:
                send_confirmation(user)
                flash("Account created for '%s'.  Please check your email for instructions on confirming your email address." % email)
            else:
                flash("Please enter a valid email address and try again.")
    else:
        if user is not None:
            # User exists, try to log them in using supplied password
            if password == '':
                flash("Please enter a password")
            else:
                pass_check = user.check_password(password)
                if pass_check:
                    login_user(user)
                    flash("Signed in as '%s'." % email)
                elif not user.is_active():
                    flash("Email address '%s' must be confirmed before logging in.  Check your email for instructions." % email)
                else:
                    flash("Incorrect password for '%s'." % email)
        else:
            flash("No account found for email address '%s'." % email)

    # Always redirect to the index page
    return redirect(url_for('index'))

@app.route('/confirm/<ObjectId:user_id>/<string:confirmation_token>', methods=['GET'])
def confirm_user(user_id, confirmation_token):
    user = db.User.find_one({ '_id' : user_id, 'confirmation_token' : unicode(confirmation_token) })
    if user is not None:
        user.confirmed = True
        user.save()
        login_user(user)
        flash("'%s' has been confirmed." % user.email)
        return redirect(url_for('set_password'))
    else:
        flash("There was an error when trying to confirm your account.")
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
