from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length
import imdb
import http.client

# Create a Flask app and configure it
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///new-books-collection.db'

# Initialize the Flask extensions
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)


# Define the Movie model
class Movie(db.Model):
    __tablename__ = 'movies'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False, unique=True)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String, nullable=False)
    img_url = db.Column(db.String, nullable=False)


# Define the form to rate a movie
class RateMovieForm(FlaskForm):
    rating = StringField('Your Rating Out of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Done')


# Define the form to add a movie
class AddMovieForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired(), Length(max=50)])
    submit = SubmitField('Add Movie')


# # Create the movies table in the database
# with app.app_context():
#     db.create_all()
#
# # Add a movie to the database
# with app.app_context():
#     new_movie = Movie(
#         title="Phone Booth",
#         year=2002,
#         description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an "
#                     "extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with "
#                     "the caller leads to a jaw-dropping climax.",
#         rating=7.3,
#         ranking=10,
#         review="My favourite character was the caller.",
#         img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
#     )
#     db.session.add(new_movie)
#     db.session.commit()


# Data-changing functions
def update_movie(movie_id, new_rating, new_review):
    """
    Updates an existing movie in the database with a new rating and review.

    Args:
        movie_id (int): The id of the movie to update.
        new_rating (float): The new rating of the movie.
        new_review (str): The new review of the movie.
    """
    with app.app_context():
        movie = Movie.query.filter_by(id=movie_id).first()
        movie.rating = new_rating
        movie.review = new_review
        db.session.commit()


def delete(movie_id):
    """
    Deletes a movie from the database.

    Args:
        movie_id (int): The id of the movie to delete.
    """
    with app.app_context():
        movie_to_delete = Movie.query.get(movie_id)
        db.session.delete(movie_to_delete)
        db.session.commit()


# Create an instance of the IMDb class with a timeout of 5 seconds
ia = imdb.IMDb(accessSystem='http', reraiseExceptions=True, timeout=5)
search_results = []


def search_movies(movie_title):
    """
    Searches for movies using the IMDb API.

    Args:
        movie_title (str): The title of the movie to search for.
    """
    global search_results
    # Search for the movie title using the search_movie() method
    search_results = None
    retries = 0
    while not search_results and retries < 3:
        try:
            search_results = ia.search_movie(movie_title)
        except http.client.IncompleteRead:
            retries += 1
            continue


def movies_titles_list():
    """
    Extracts the titles of the movies from the search results.

    Returns:
        list: A list of strings containing the titles of the movies.
    """
    global search_results

    movies_titles = []
    for result in search_results:
        movies_titles.append(f"{result['title']} ({result['year']})")

    return movies_titles


def get_movie_details(selection):
    """
    Gets the details of a movie using the IMDb API.

    Args:
        selection (int): The index of the selected movie in the search results.

    Returns:
        dict: A dictionary containing the details of the movie.
    """
    global search_results
    # Get the movie details using the get_movie() method
    movie_id = search_results[selection - 1].getID()
    movie_details = None
    retries = 0
    while not movie_details and retries < 3:
        try:
            movie_details = ia.get_movie(movie_id)
        except http.client.IncompleteRead:
            retries += 1
            continue

    return movie_details


# Define the routes of the Flask app
@app.route("/")
def home():
    """
    Renders the home page of the app.

    Returns:
        str: The HTML content of the home page.
    """
    all_movies = db.session.query(Movie).all()

    return render_template("index.html", all_movies=all_movies)


@app.route("/edit_movie/<int:movie_id>", methods=["POST", "GET"])
def edit_movie(movie_id):
    """
    Renders the page to edit the rating and review of a movie.

    Args:
        movie_id (int): The id of the movie to edit.

    Returns:
        str: The HTML content of the edit page.
    """
    update_form = RateMovieForm()
    if update_form.validate_on_submit():
        new_rating = update_form.rating.data
        new_review = update_form.review.data
        update_movie(movie_id, new_rating, new_review)

        return redirect(url_for('home'))

    return render_template("edit.html", update_form=update_form)


@app.route("/delete_movie/<int:movie_id>")
def delete_movie(movie_id):
    """
    Deletes a movie from the database.

    Args:
        movie_id (int): The id of the movie to delete.

    Returns:
        str: A redirect to the home page.
    """
    delete(movie_id)

    return redirect(url_for("home"))


@app.route("/add_movie", methods=["POST", "GET"])
def add_movie():
    """
    Renders the page to add a movie to the database.

    Returns:
        str: The HTML content of the add page.
    """
    add_form = AddMovieForm()
    if add_form.validate_on_submit():
        movie_title = add_form.title.data
        search_movies(movie_title)
        movies_data = movies_titles_list()

        return render_template("select.html", movies_data=movies_data)

    return render_template("add.html", add_form=add_form)


@app.route("/add_movie/<int:selection>/<movie_title>", methods=["POST", "GET"])
def select_movie(selection, movie_title):
    """
    Renders the page to select a movie from the search results.

    Args:
        selection (int): The index of the selected movie in the search results.
        movie_title (str): The title of the movie to add.

    Returns:
        str: The HTML content of the movie page.
    """
    movie_details = get_movie_details(selection)

    return render_template("movie.html", movie_title=movie_title, movie_details=movie_details)


# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
