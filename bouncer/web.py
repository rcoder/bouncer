# Copyright 2013 by Urban Airship and Lennon Day-Reynolds <lennon@urbanairship.com>
# See license information in COPYING.

import re

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

from bouncer.db import q, iq

# Generic helpers

def make_url_dict(row):
  url_id, slug, full_url, clicks, ctime, atime = row
  url_dict = {
    'url_id': url_id,
    'slug': slug,
    'full_url': full_url,
    'clicks': clicks,
    'ctime': ctime,
    'atime': atime
  }
  return url_dict

def load_url_info(url_id):
  url_dict = None
  sql = 'select rowid, slug, full_url, clicks, ctime, atime from urls where rowid = ?'
  with q(sql, url_id) as c:
    result = c.fetchone()
    if result is not None:
      url_dict = make_url_dict(result)
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

def top_n_urls(order_by, limit=10):
  sql = '''
    select rowid, slug, full_url, clicks, ctime, atime
    from urls
    order by {} desc
  limit {}'''.format(order_by, limit)
  results = []

  with q(sql) as c:
    for row in c:
      url_dict = make_url_dict(row)
      results.append(url_dict)

  return results

def validate_slug(slug):
  if slug in app.view_functions:
    raise ValueError('cannot use an existing view name ({}) as a slug')
  elif not re.match(r'^[-\w/_\.]+$', slug):
    raise ValueError('invalid characters in slug')

# Actual app routes start here

@app.route('/')
def home():
  limit = 10

  recent = top_n_urls('rowid', limit)
  active = top_n_urls('atime', limit)
  clicks = top_n_urls('clicks', limit)

  size_of_lists = max([len(x) for x in (recent, active, clicks)])

  return render_template('home.html',
    recent=recent, active=active, clicks=clicks,
    size_of_lists=size_of_lists)

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
      num_vars = len(url_pattern.split('{}')) - 1
      gaps = num_vars - len(pieces)
      pieces += ([''] * gaps)
      full_url = url_pattern.format(*[str(p) for p in pieces])
      c.execute('''
        update urls set atime = current_timestamp,
        clicks = (clicks + 1) where rowid = ?
      ''', str(url_id))
      return redirect(full_url)

@app.route('/new', methods=['GET', 'POST'])
def new():
  if request.method == 'POST':
    slug = request.form['slug']
    validate_slug(slug)
    full_url = request.form['full_url']
    url_id = iq('insert into urls(slug, full_url) values(?, ?)', slug, full_url)
    return redirect(url_for('show', url_id=url_id))
  else:
    return render_template('edit.html', url={}, target=url_for('new'))

@app.route('/edit/<int:url_id>', methods=['GET', 'POST'])
def edit(url_id):
  if request.method == 'POST':
    slug = request.form['slug']
    validate_slug(slug)
    full_url = request.form['full_url']
    iq('update urls set slug = ?, full_url = ? where rowid = ?', slug, full_url, url_id)
    return redirect(url_for('show', url_id=url_id))
  else:
    params = {'target': url_for('edit', url_id=url_id)}
    return render_template_with_url('edit.html', url_id, params)

@app.route('/show/<int:url_id>')
def show(url_id):
  return render_template_with_url('show.html', url_id)

@app.route('/delete', methods=['POST'])
def delete():
  url_id = request.form['url_id']
  confirm = request.form['yes_i_mean_it']
  if confirm == 'y':
    iq('delete from urls where rowid = ?', url_id)
  return redirect('/')

@app.route('/find')
def find():
  search = request.args.get('q')
  results = []
  if search is None:
    return 'Search filter cannot be empty!', 400
  else:
    sql = 'select rowid, slug, full_url, clicks, ctime, atime from urls where slug like ?'
    with q(sql, '%'+search+'%') as c:
      results = [make_url_dict(row) for row in c.fetchmany()]
      return render_template('list.html', results=results, search=search)


