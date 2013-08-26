from contextlib import contextmanager
from flask import Flask, redirect, render_template, request, url_for

import sqlite3

app = Flask(__name__)

# Database helper functions (we don't need no steenkin' ORM!)

@contextmanager
def dbopen():
  db = sqlite3.connect('bouncer.db')
  try:
    yield db
  finally:
    db.close()

@contextmanager
def dbcursor(db):
  c = db.cursor()
  try:
    yield c
  finally:
    c.close()

@contextmanager
def q(q, *params):
  'Perform a DB query, yield the active cursor, then commit'
  with dbopen() as db, dbcursor(db) as c:
    c.execute(q, params)
    yield c
    db.commit()

def iq(q, *params):
  'Execute a query, commit, and return the last insert row'
  with dbopen() as db, dbcursor(db) as c:
    rowid = None
    c.execute(q, params)
    db.commit()
    rowid = c.lastrowid
  return rowid

# Generic helpers

def load_url_info(url_id):
  url_dict = None
  sql = 'select slug, full_url, clicks, ctime, atime from urls where rowid = ?'
  with q(sql, url_id) as c:
    result = c.fetchone()
    if result is not None:
      slug, full_url, clicks, ctime, atime = result
      url_dict = {
        'slug': slug,
        'full_url': full_url,
        'clicks': clicks,
        'ctime': ctime,
        'atime': atime
      }
  return url_dict

def render_template_with_url(template, url_id, params=None, url_param_name='url'):
  if params is None:
    params = {}

  url_dict = load_url_info(url_id)

  if url_dict is None:
    return 'No such URL (id={}) found'.format(url_id), 404
  else:
    params[url_param_name] = url_dict
    return render_template(template, **params)

# Actual app routes start here

@app.route('/')
def index():
  return 'ok'

@app.route('/<path:p>')
def go(p):
  pieces = p.split('/')
  slug = pieces.pop(0)
  with q('select rowid, full_url from urls where slug = ?', slug) as c:
    result = c.fetchone()
    if result is None:
      return 'No such link ({}) found'.format(p), 404
    else:
      url_id, url_pattern = result
      full_url = url_pattern.format(pieces)
      c.execute('''
        update urls set atime = current_timestamp,
        clicks = (clicks + 1) where rowid = ?
      ''', str(url_id))
      return redirect(full_url)

@app.route('/new', methods=['GET', 'POST'])
def new():
  if request.method == 'POST':
    slug = request.form['slug']
    full_url = request.form['full_url']
    url_id = iq('insert into urls(slug, full_url) values(?, ?)', slug, full_url)
    return redirect(url_for('show', url_id=url_id))
  else:
    return render_template('edit.html', target=url_for('new'))

@app.route('/edit/<int:url_id>')
def edit(url_id):
  if request.method == 'POST':
    slug = request.form['slug']
    full_url = request.form['full_url']
    q('update urls set slug = ?, full_url = ? where rowid = ?', slug, full_url, url_id)
    return redirect(url_for('show', url_id=url_id))
  else:
    params = {'target': url_for('edit', url_id=url_id)}
    return render_template_with_url('edit.html', url_id, params)

@app.route('/show/<int:url_id>')
def show(url_id):
  return render_template_with_url('show.html', url_id)

@app.route('/delete', methods=['POST'])
def delete():
  pass

@app.route('/find')
def find():
  search = request.args.get('q')
  results = []
  if q is None:
    return 'Search filter cannot be empty!', 400
  else:
    with q('select rowid, slug, full_url from urls where slug like ?', '%'+search+'%') as c:
      results = c.fetchmany()
      return render_template('list.html', results=results)

if __name__ == '__main__':
  app.debug = True
  app.run()

