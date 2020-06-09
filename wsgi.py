import os
import uuid
import logging
import markdown2
from datetime import datetime
from logging.config import dictConfig
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, make_response
from db import get_session, Post, Link, Visit

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY ')

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


@app.route('/<uid>')
def view(uid):
    # import ipdb; ipdb.set_trace()
    s = get_session()
    link = s.query(Link).filter_by(uid=uid).one()
    title = link.post.title
    md = markdown2.markdown(link.post.body)
    s.add(Visit(link_id=link.id,
                dt=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                ip=request.remote_addr,
                ref=request.referrer))
    s.commit()
    s.close()
    resp = make_response(render_template('post.html', body=md, title=title))
    resp.headers['Referrer-Policy'] = 'unsafe-url'
    return resp

@app.route('/info/<pid>')
def info(pid):
    s = get_session()
    post = s.query(Post).filter_by(id=pid).one()
    title = post.title
    md = post.body
    links = list([{
        'link_for': link.link_for,
        'href': url_for('view', uid=link.uid, _external=True),
        'visits': [{
            'dt': v.dt,
            'ip': v.ip,
            'ref': v.ref
        } for v in link.visits]
    } for link in post.links])
    s.close()
    return render_template('info.html', title=title, md=md, links=links)

@app.route('/admin')
def admin():
    s = get_session()
    posts = [(p.id, p.title) for p in s.query(Post).all()]
    s.close()
    logging.info(posts)
    return render_template('admin.html', posts=posts)

@app.route('/newlink', methods=['POST'])
def newlink():
    uid = str(uuid.uuid1()).replace('-','')
    link_for = request.form['linkfor']
    post_id = int(request.form['post_id'])
    s = get_session()
    link = Link(link_for=link_for, uid=uid, post_id=post_id)
    s.add(link)
    s.commit()
    s.close()
    logging.info(link)
    flash('Link added for {}: {}'.format(link_for, url_for('view', uid=uid, _external=True)))
    return redirect(url_for('admin'))

@app.route('/send', methods=['POST'])
def send():
    title = request.form['title']
    body = request.form['md']
    logging.info('Making post: %s', title)
    s = get_session()
    s.add(Post(title=title, body=body))
    s.commit()
    s.close()
    return redirect(url_for('admin'))

if __name__ == "__main__":
    app.run()
