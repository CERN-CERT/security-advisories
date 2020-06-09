import os
import hashlib
import uuid
import logging
import markdown2
from datetime import datetime
from logging.config import dictConfig
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, make_response
from db import get_session, Post, Link, Visit

application = Flask(__name__)
application.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
application.config['SERVER_NAME'] = os.getenv('SERVER_NAME')
application.config['PREFERRED_URL_SCHEME'] = 'https'

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

@application.route('/sekkreturl/info/<pid>')
def info(pid):
    s = get_session()
    try:
        post = s.query(Post).filter_by(id=pid).one()
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

@application.route('/sekkreturl/admin')
def admin():
    s = get_session()
    posts = [(p.id, p.title) for p in s.query(Post).all()]
    s.close()
    logging.info(posts)
    return render_template('admin.html', posts=posts)

@application.route('/sekkreturl/newlink', methods=['POST'])
def newlink():
    uid = str(uuid.uuid1()).replace('-','')
    link_for = request.form['linkfor']
    post_id = int(request.form['post_id'])
    s = get_session()
    try:
        link = Link(link_for=link_for, uid=uid, post_id=post_id)
        s.add(link)
        s.commit()
        logging.info(link)
        flash('Link added for {}: {}'.format(link_for, url_for('view', uid=uid, _external=True, _scheme='https')))
        return redirect(url_for('admin', _scheme='https'))
    finally:
        s.close()

@application.route('/sekkreturl/send', methods=['POST'])
def send():
    title = request.form['title']
    body = request.form['md']
    logging.info('Making post: %s', title)
    s = get_session()
    try:
        s.add(Post(title=title, body=body))
        s.commit()
        return redirect(url_for('admin', _scheme='https'))
    finally:
        s.close()

@application.route('/<uid>')
def view(uid):
    logging.info('Viewing uid %s', uid)
    s = get_session()
    try:
        link = s.query(Link).filter_by(uid=uid).first()
        if link is None:
            return '', 404
        title = link.post.title
        md = markdown2.markdown(link.post.body)
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
