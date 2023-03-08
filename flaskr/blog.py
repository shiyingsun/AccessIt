from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)


@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username, reputation,latlng,address'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        latlng = request.form['latlng']
        address = request.form['address']
        error = None

        if not title:
            error = 'Title is required.'

        if not latlng:
            error = 'Pleas enter place reviewed.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id,latlng,address)'
                ' VALUES (?, ?, ?,?, ?)',
                (title, body, g.user['id'], latlng, address)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')


def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username,reputation,latlng, address'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))


@bp.route('/googlemaps', methods=('POST', 'GET'))
def googlemaps():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username, reputation, latlng, address'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/googlemaps.html', posts=posts)
    return redirect(url_for('blog.index'))

@bp.route('/voting/<int:id>', methods=('POST',))
@login_required
def voting(id):
    post = get_post(id)
    reputation = post['reputation']
    if request.method == 'POST':
        if request.form['votebutton'] == 'upvote':
            db = get_db()
            db.execute(
                'UPDATE post '
                'SET reputation = (reputation+1) '
                'WHERE id = ?',
                (id,)
            )
            db.commit()
        elif request.form['votebutton'] == 'downvote':
            if reputation > 0:
                db = get_db()
                db.execute(
                    'UPDATE post '
                    'SET reputation = (reputation-1) '
                    'WHERE id = ?',
                    (id,)
                )
                db.commit()
            else:
                flash("Reputation cannot go below 0")
        return redirect("/")
