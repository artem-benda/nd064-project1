import sqlite3
import logging
import threading

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

threadLock = threading.Lock()
connections_counter = 0


def inc_connections_counter():
    global connections_counter
    with threadLock:
        connections_counter += 1


def dec_connections_counter():
    global connections_counter
    with threadLock:
        connections_counter -= 1


# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection


# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    inc_connections_counter()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                              (post_id,)).fetchone()
    connection.close()
    dec_connections_counter()
    return post


# Function to get a post using its ID
def get_posts_count():
    connection = get_db_connection()
    inc_connections_counter()
    posts_count = connection.execute('SELECT count(*) FROM posts').fetchone()[0]
    connection.close()
    dec_connections_counter()
    return posts_count


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'


# Define the main route of the web application
@app.route('/')
def index():
    connection = get_db_connection()
    inc_connections_counter()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    dec_connections_counter()
    app.logger.info('Root request successful, showing {} posts'.format(len(posts)))
    return render_template('index.html', posts=posts)


# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.info('Post with id {} not found, showing 404 page'.format(post_id))
        return render_template('404.html'), 404
    else:
        app.logger.info('Post [id={}, title={}] found successfully, showing post page'.format(post_id, post['title']))
        return render_template('post.html', post=post)


# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('About request successful')
    return render_template('about.html')


# Define the post creation functionality
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            inc_connections_counter()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                               (title, content))
            connection.commit()
            connection.close()
            dec_connections_counter()

            app.logger.info('New post [title={}] created successfully'.format(title))
            return redirect(url_for('index'))

    return render_template('create.html')


# Health endpoint
@app.route('/healthz')
def health():
    response = app.response_class(
        response=json.dumps({"result": "OK - healthy"}),
        status=200,
        mimetype='application/json'
    )

    app.logger.info('Status request successful')
    return response


@app.route('/metrics')
def metrics():
    posts_count = get_posts_count()

    response = app.response_class(
        response=json.dumps({"db_connection_count": connections_counter, "post_count": posts_count}),
        status=200,
        mimetype='application/json'
    )

    app.logger.info('Metrics request successful')
    return response


# start the application on port 3111
if __name__ == "__main__":
    # stream logs to a file
    logging.basicConfig(
        filename='app.log',
        level=logging.DEBUG,
        format='%(levelname)s:%(module)s:%(funcName)s %(asctime)s.%(msecs)03d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logging.getLogger().addHandler(logging.StreamHandler())

    app.run(host='0.0.0.0', port='3111')
