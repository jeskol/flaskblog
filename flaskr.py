#! /usr/bin/env python

# all the imports
import sqlite3
from contextlib import closing
from math import ceil
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash

# default configuration
DATABASE = 'flaskr.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'
MAIN_PAGE_COUNT = 3

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

app.config.from_envvar('FLASKR_SETTINGS', silent=False)

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def max_pages():
    result = g.db.execute('select count(*) from entries')
    total_posts = int(result.fetchall()[0][0])
    max_pages = ceil(float(total_posts) / float(MAIN_PAGE_COUNT))
    return int(max_pages)

@app.route('/')
@app.route('/page/<page>')
def show_entries(page=1):
    page = int(page)
    pagination = dict(max_pages=max_pages(), page=page, next=(page + 1), prev=(page -1))
    offset = pagination['prev'] * MAIN_PAGE_COUNT
    cur = g.db.execute('select id, title, text, modified from entries order by created desc limit %s offset %s'%(MAIN_PAGE_COUNT, offset))
    entries = [dict(postid=row[0], title=row[1], text=row[2], modified=row[3]) for row in cur.fetchall()]
    return render_template('show_entries.html', entries=entries, pagination=pagination)

@app.route('/post/<postid>')
def show_post(postid):
    pagination = dict(max_pages=1)
    db_results = g.db.execute('select id, title, text, modified from entries where id = ?', postid)
    entries = [dict(postid=row[0], title=row[1], text=row[2], modified=row[3]) for row in db_results.fetchall()]
    return render_template('show_entries.html', entries=entries, pagination=pagination)

@app.route('/list')
def list_entries():
    list_results = g.db.execute('select id, title, modified from entries order by created desc')
    entries = [dict(postid=row[0], title=row[1], modified=row[2]) for row in list_results.fetchall()]
    return render_template('list_entries.html', entries=entries)

@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('insert into entries (title, text) values (?, ?)',
                 [request.form['title'], request.form['text']])
    g.db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))

@app.route('/edit/<postid>', methods=['GET', 'POST'])
def edit_entry(postid):
    if not session.get('logged_in'):
        abort(401)
    if request.method == 'POST':
        g.db.execute('update entries set title = ?, text = ?, modified=datetime(\'now\') where id = ?',
                 [request.form['title'], request.form['text'], postid])
        g.db.commit()
        flash('Entry was successfully updated')
        return redirect(url_for('show_post', postid=postid))
    db_results = g.db.execute('select id, title, text, modified from entries where id = ?', postid)
    entry = dict()
    for row in db_results.fetchall():
        entry = { 'postid' : row[0],
                  'title' : row[1],
                  'text' : row[2],
                  'modified' : row[3] 
                }
    return render_template('edit_entry.html', entry=entry)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))



if __name__ == '__main__':
    app.run()

