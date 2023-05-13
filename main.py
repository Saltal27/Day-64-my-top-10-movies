from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length
import requests
import concurrent.futures

movies_details = []

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
# Add a movie to the database
def add_movie_db(title, year, description, rating, ranking, review, img_url):
    """
    Adds a movie to the database.

    Args:
        title (str): The title of the movie.
        year (int): The year the movie was released.
        description (str): A brief description of the movie.
        rating (float): The rating of the movie.
        ranking (int): The ranking of the movie.
        review (str): A review of the movie.
        img_url (str): The URL of the movie's poster image.
    """
    with app.app_context():
        new_movie = Movie(
            title=title,
            year=year,
            description=description,
            rating=rating,
            ranking=ranking,
            review=review,
            img_url=img_url
        )
        db.session.add(new_movie)
        db.session.commit()


# Data-changing functions
def update_movie_db(db_movie_id, new_rating, new_review):
    """
    Updates an existing movie_to_update in the database with a new rating and review.

    Args:
        db_movie_id (int): The id of the movie_to_update to update.
        new_rating (float): The new rating of the movie_to_update.
        new_review (str): The new review of the movie_to_update.
    """
    with app.app_context():
        movie_to_update = Movie.query.filter_by(id=db_movie_id).first()
        movie_to_update.rating = new_rating
        movie_to_update.review = new_review
        db.session.commit()


def delete_movie_db(db_movie_id):
    """
    Deletes a movie from the database.

    Args:
        db_movie_id (int): The id of the movie to delete.
    """
    with app.app_context():
        movie_to_delete = Movie.query.get(db_movie_id)
        db.session.delete(movie_to_delete)
        db.session.commit()


def order_movies_db():
    """
    Orders the movies in the database by their rating.
    """
    with app.app_context():
        movies = Movie.query.all()
        sorted_movies = sorted(movies, key=lambda x: x.rating, reverse=True)

        # update the ranking attribute of each movie based on its order
        for i, movie in enumerate(sorted_movies):
            movie.ranking = i + 1
            db.session.commit()

    return sorted_movies


# searching for the movie
def search_movies(title):
    """
    Searches for movies using the OMDb API.

    Args:
        title (str): The title of the movie to search for.

    Returns:
        list: A list of movie objects containing the search results.
    """
    # Make a GET request to the OMDb API with the movie title as a parameter
    response = requests.get('http://www.omdbapi.com/', params={'apikey': '6c82bc54', 's': title})

    # Parse the JSON response and return the search results
    data = response.json()
    if data['Response'] == 'True':
        return data['Search']
    else:
        return []


def get_movie_details(imdb_movie_id):
    """
    Gets the details of a movie using the OMDb API.

    Args:
        imdb_movie_id (str): The ID of the movie to retrieve.

    Returns:
        dict: A dictionary containing the details of the movie.
    """
    # Make a GET request to the OMDb API with the movie ID as a parameter
    response = requests.get('http://www.omdbapi.com/', params={'apikey': '6c82bc54', 'i': imdb_movie_id})

    # Parse the JSON response and return the movie details
    return response.json()


def search_and_retrieve(title):
    """
    Searches for a movie and retrieves its details using the OMDb API.

    Args:
        title (str): The title of the movie to search for.

    Returns:
        list: A list of dictionaries containing the details of the movies.
    """
    # Search for the movie title
    search_results = search_movies(title)

    # Retrieve the details of the movies using multiple threads
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Create a list of futures for each movie in the search results
        futures = [executor.submit(get_movie_details, result['imdbID']) for result in search_results]

        # Wait for all futures to complete and get the results
        details = [future.result() for future in concurrent.futures.as_completed(futures)]

    # Return the details of the movies
    return details


# Define the routes of the Flask app
@app.route("/")
def home():
    """
    Renders the home page of the app.

    Returns:
        str: The HTML content of the home page.
    """
    with app.app_context():
        movies = Movie.query.all()
        sorted_movies = sorted(movies, key=lambda x: x.rating, reverse=True)

        # update the ranking attribute of each movie based on its order
        for i, movie in enumerate(sorted_movies):
            movie.ranking = i + 1

    return render_template("index.html", all_movies=sorted_movies)


@app.route("/edit_movie/<int:db_movie_id>", methods=["POST", "GET"])
def edit_movie(db_movie_id):
    """
    Renders the page to edit the rating and review of a movie.

    Args:
        db_movie_id (int): The id of the movie to edit.

    Returns:
        str: The HTML content of the edit page.
    """
    update_form = RateMovieForm()
    if update_form.validate_on_submit():
        new_rating = update_form.rating.data
        new_review = update_form.review.data
        update_movie_db(db_movie_id, new_rating, new_review)

        order_movies_db()
        return redirect(url_for('home'))

    return render_template("edit.html", update_form=update_form)


@app.route("/delete_movie/<int:db_movie_id>")
def delete_movie(db_movie_id):
    """
    Deletes a movie from the database.

    Args:
        db_movie_id (int): The id of the movie to delete.

    Returns:
        str: A redirect to the home page.
    """
    delete_movie_db(db_movie_id)
    order_movies_db()

    return redirect(url_for("home"))


@app.route("/add_movie", methods=["POST", "GET"])
def add_movie():
    """
    Renders the page to add a movie to the database.

    Returns:
        str: The HTML content of the add page.
    """
    global movies_details

    add_form = AddMovieForm()
    if add_form.validate_on_submit():
        movie_title = add_form.title.data
        movies_details = search_and_retrieve(movie_title)
        movie_titles_list = []
        for movie in movies_details:
            if movie['Type'] == "movie":
                movie_titles_list.append(f"{movie['Title']} - ({movie['Year']})")

        return render_template("select.html", movie_titles_list=movie_titles_list)

    return render_template("add.html", add_form=add_form)


@app.route("/add_movie/<int:movie_index>/<selected_movie_title>", methods=["POST", "GET"])
def select_movie(movie_index, selected_movie_title):
    """
    Renders the page to select a movie from the search results.

    Args:
        movie_index (int): the index of the selected movie title in the movies titles list.
        selected_movie_title (str): The title of the movie to add.

    Returns:
        str: The HTML content of the movie page.
    """

    global movies_details

    movie = movies_details[movie_index]

    genres = movie['Genre']
    rating = movie['imdbRating']
    description = movie['Plot']
    poster_url = movie['Poster']
    selected_movie_title_no_year = selected_movie_title.split(" - (")[0]

    return render_template(
        "movie.html",
        selected_movie_title=selected_movie_title,
        genres=genres,
        rating=rating,
        description=description,
        poster_url=poster_url,
        selected_movie_title_no_year=selected_movie_title_no_year,
        movie_index=movie_index
    )


@app.route("/submit_movie/<selected_movie_title_no_year>/<int:movie_index>")
def submit_movie(selected_movie_title_no_year, movie_index):
    """
    Adds a movie to the database.

    Args:
        selected_movie_title_no_year (str): The title of the movie to add.
        movie_index (int): the index of the selected movie title in the movies titles list.

    Returns:
        str: A redirect to the home page.
    """

    global movies_details

    movie = movies_details[movie_index]

    year = movie['Year']
    description = movie['Plot']
    rating = movie['imdbRating']
    ranking = 0
    review = "none"
    poster_url = movie['Poster']

    add_movie_db(selected_movie_title_no_year, year, description, rating, ranking, review, poster_url)

    # find the movie db_id
    movie = Movie.query.filter_by(title=selected_movie_title_no_year).first()

    db_movie_id = movie.id
    return redirect(url_for("edit_movie", db_movie_id=db_movie_id))


# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
