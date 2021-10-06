import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
import logging


# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global dbCount
    dbCount += 1
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    global dbConnectionError
    connection = get_db_connection()
    try:
        post = connection.execute('SELECT * FROM posts WHERE id = ?',
                            (post_id,)).fetchone()
    except sqlite3.Error as e:
        dbConnectionError = True
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'
dbCount = 0
dbConnectionError = False


# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    global dbConnectionError
    try:
        posts = connection.execute('SELECT * FROM posts').fetchall()
    except sqlite3.Error as e:
        dbConnectionError = True
        return
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      app.logger.error('A non existing article is accessed and a 404 page is returned')
      return render_template('404.html'), 404
    else:
      app.logger.info('Article "{}" retrieved!'.format(post['title']))
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('The "About Us" page is retrieved')
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
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()

            return redirect(url_for('index'))

    return render_template('create.html')

# Define the health check endpoint
@app.route('/healthz', methods=('GET', 'POST'))
def health():
    global dbConnectionError
    if(dbConnectionError == True):
        response = app.response_class(
        response=json.dumps({"result":"ERROR - unhealthy"}),
        status=500,
        mimetype='application/json')
    else:
        response = app.response_class(
        response=json.dumps({"result":"OK - healthy"}),
        status=200,
        mimetype='application/json')

    return response

# Define the metrics endpoint
@app.route('/metrics', methods=('GET', 'POST'))
def metrics():
    global dbCount
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    postCounts = len(posts)
    connection.close()
    response = app.response_class(
        response=json.dumps({"db_connection_count": dbCount, "post_count": postCounts}),
        status=200,
        mimetype='application/json'
    )
    return response


# start the application on port 3111
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    app.run(host='0.0.0.0', port='3111')
