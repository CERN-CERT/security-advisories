import hashlib
import uuid
import logging
import markdown
import pytz
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from werkzeug.middleware.proxy_fix import ProxyFix

from db import get_session, Post, Link, Visit
from config import SECRET_KEY, SERVER_NAME


application = Flask(__name__)
application.wsgi_app = ProxyFix(application.wsgi_app, x_for=2, x_proto=2, x_host=2, x_port=2, x_prefix=2)

application.config['SECRET_KEY'] = SECRET_KEY
application.config['SERVER_NAME'] = SERVER_NAME


@application.route('/admin/info/<pid>', methods=['GET', 'POST'])
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
            'id': link.id,
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


@application.route('/admin')
def admin():
    s = get_session()
    posts = [(p.id, p.title) for p in s.query(Post).all()]
    s.close()
    logging.info(posts)
    return render_template('admin.html', posts=posts)


@application.route('/admin/newlink', methods=['POST'])
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


@application.route('/admin/dellink/<linkid>', methods=['POST'])
def dellink(linkid):
    s = get_session()
    try:
        link = s.query(Link).filter_by(id=linkid).one()
        if request.form['action'] == 'Delete':
            s.delete(link)
            s.commit()
        return redirect(url_for('admin'))
    finally:
        s.close()


@application.route('/admin/send', methods=['POST'])
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
                    dt=datetime.now(pytz.timezone('Europe/Zurich')).strftime('%Y-%m-%d %H:%M:%S'),
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
