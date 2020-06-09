import os
import hashlib
import uuid
import logging
import markdown
from datetime import datetime
from logging.config import dictConfig
from flask import Flask, render_template, request, redirect, url_for, flash, make_response, current_app
from db import get_session, Post, Link, Visit
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_dance.consumer import OAuth2ConsumerBlueprint
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError, TokenExpiredError


# dictConfig({
    # 'version': 1,
    # 'formatters': {'default': {
        # 'format': '[%(asctime)s] %(levelname)s: %(message)s',
    # }},
    # 'handlers': {'wsgi': {
        # 'class': 'logging.StreamHandler',
        # 'stream': 'ext://flask.logging.wsgi_errors_stream',
        # 'formatter': 'default'
    # }},
    # 'root': {
        # 'level': 'INFO',
        # 'handlers': ['wsgi']
    # }
# })


application = Flask(__name__)
application.wsgi_app = ProxyFix(application.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

application.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
application.config['SERVER_NAME'] = os.getenv('SERVER_NAME')


# oauth = OAuth2ConsumerBlueprint(
    # 'cern_oauth',
    # __name__,
    # client_id=os.getenv('OAUTH_CLIENT_ID'),
    # client_secret=os.getenv('OAUTH_CLIENT_SECRET'),
    # token_url='https://oauth.web.cern.ch/OAuth/Token',
    # authorization_url='https://oauth.web.cern.ch/OAuth/Authorize',
    # login_url='/oauth/cern',
    # authorized_url='/oauth/cern/authorized',
# )
# application.oauth = oauth
# application.register_blueprint(oauth)


# def require_auth(func):
    # def wrapper(*args, **kwargs):
        # return func(*args, **kwargs)
        # if current_app.oauth.token:
            # try:
                # user_details = oauth.session.get(
                    # 'https://oauthresource.web.cern.ch/api/User')
                # user_details.raise_for_status()
                # # user_data = user_details.json()
                # # username = user_data['username'].strip()
                # egroup_membership = current_app.oauth.session.get(
                    # 'https://oauthresource.web.cern.ch/api/Groups')
                # egroup_membership.raise_for_status()
                # groups = egroup_membership.json()['groups']
                # logging.debug('OAuth groups: %s', groups)
                # if any(group in groups for group in current_app.config['app']['auth_egroups']):
                    # return func(*args, **kwargs)
                # else:
                    # return 'Unauthorized', 401
            # except (InvalidGrantError, TokenExpiredError) as e:
                # logging.warn(e)
                # pass
        # return redirect(url_for('cern_oauth.login'))
    # wrapper.func_name = func.func_name
    # return wrapper


# @require_auth
@application.route('/sekkreturl/info/<pid>', methods=['GET', 'POST'])
def info(pid):
    s = get_session()
    try:
        post = s.query(Post).filter_by(id=pid).one()
        if request.method == 'POST':
            if request.form['action'] == 'Delete':
                s.delete(post)
                s.commit()
                return redirect(url_for('admin'))
            else:
                post.title = request.form['title']
                post.body = request.form['body']
                s.commit()
        title = post.title
        md = post.body
        links = list([{
            'link_for': link.link_for,
            'href': url_for('view', uid=link.uid, _external=True, _scheme='https'),
            'visits': [{
                'dt': v.dt,
                'ip': v.ip,
                'ref': v.ref
            } for v in link.visits]
        } for link in post.links])
        return render_template('info.html', title=title, md=md, links=links)
    finally:
        s.close()


# @require_auth
@application.route('/sekkreturl/admin')
def admin():
    s = get_session()
    posts = [(p.id, p.title) for p in s.query(Post).all()]
    s.close()
    logging.info(posts)
    return render_template('admin.html', posts=posts)


# @require_auth
@application.route('/sekkreturl/newlink', methods=['POST'])
def newlink():
    uid = str(uuid.uuid1()).replace('-', '')
    link_for = request.form['linkfor']
    post_id = int(request.form['post_id'])
    s = get_session()
    try:
        link = Link(link_for=link_for, uid=uid, post_id=post_id)
        s.add(link)
        s.commit()
        logging.info(link)
        flash('Link added for {}: {}'.format(link_for, url_for('view', uid=uid, _external=True, _scheme='https')))
        return redirect(url_for('admin'))
    finally:
        s.close()


# @require_auth
@application.route('/sekkreturl/send', methods=['POST'])
def send():
    title = request.form['title']
    body = request.form['md']
    logging.info('Making post: %s', title)
    s = get_session()
    try:
        s.add(Post(title=title, body=body))
        s.commit()
        return redirect(url_for('admin'))
    finally:
        s.close()


@application.route('/<uid>')
def view(uid):
    logging.info('Viewing uid %s ip %s ref %s', uid, request.remote_addr, request.referrer)
    s = get_session()
    try:
        link = s.query(Link).filter_by(uid=uid).first()
        if link is None:
            return '', 404
        title = link.post.title
        md = markdown.markdown(link.post.body, extensions=['tables', 'fenced_code', 'sane_lists'])
        s.add(Visit(link_id=link.id,
                    dt=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    ip=request.remote_addr,
                    ref=request.referrer))
        s.commit()
        tracker = hashlib.sha256(uid.encode()).hexdigest()[:16]
        resp = make_response(render_template('post.html', body=md, title=title, tracker=tracker))
        resp.headers['Referrer-Policy'] = 'unsafe-url'
        return resp
    finally:
        s.close()


if __name__ == "__main__":
    application.run()
