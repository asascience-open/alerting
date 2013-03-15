from flask import request, url_for, render_template, redirect, session, flash
from alerting import db, app, facebook, google
from json import loads
from werkzeug import url_encode
from urllib2 import Request, urlopen, URLError


@app.route('/logout')
def logout():
    session.pop('facebook_token', None)
    session.pop('google_token', None)
    session.pop('user_email', None)

    flash('Signed out')
    return redirect(request.referrer or url_for('index'))

# FACEBOOK
@app.route('/login_facebook')
def login_facebook():
    return facebook.authorize(callback=url_for('facebook_authorized',
                              next=request.args.get('next') or request.referrer or None,
                              _external=True))

@app.route('/login/facebook_authorized')
@facebook.authorized_handler
def facebook_authorized(resp):
    if resp is None:
        flash('Access denied')
        return redirect(url_for('index'))

    session['facebook_token'] = (resp['access_token'], '')
    #request 'me' to get user id and email
    me = facebook.get('/me')
    session['user_email'] = me.data['email']
    
    #flash("Signed in as %s" % session.get('user_email'))

    next_url = request.args.get('next') or url_for('index')
    return redirect(next_url)

@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('facebook_token')

#GOOGLE
@app.route('/login_google')
def login_google():
    return google.authorize(callback=url_for('google_authorized',_external=True))

@app.route('/login/google_authorized')
@google.authorized_handler
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
        session['user_email'] = loads(res.read()).get(u'email')
        flash("Signed in as %s" % session.get('user_email'))
        next_url = request.referrer or url_for('index')
        return redirect(next_url)
    except URLError, e:
        if e.code == 401:
            # Unauthorized - bad token
            session.pop('google_token', None)
            flash('Unauthoirzed')
            return redirect(url_for('index'))