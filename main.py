from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length
import imdb
import http.client


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///new-books-collection.db'
db = SQLAlchemy(app)


# Create the movies table in the database
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


# Flask-WTForms
class RateMovieForm(FlaskForm):
    rating = StringField('Your Rating Out of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Done')


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
    with app.app_context():
        movie = Movie.query.filter_by(id=movie_id).first()
        movie.rating = new_rating
        movie.review = new_review
        db.session.commit()


def delete(movie_id):
    with app.app_context():
        movie_to_delete = Movie.query.get(movie_id)
        db.session.delete(movie_to_delete)
        db.session.commit()


# Create an instance of the IMDb class with a timeout of 5 seconds
ia = imdb.IMDb(accessSystem='http', reraiseExceptions=True, timeout=5)
search_results = []


def search_movies(movie_title):
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
    global search_results

    movies_titles = []
    for result in search_results:
        movies_titles.append(f"{result['title']} ({result['year']})")

    return movies_titles


def get_movie_details(selection):
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


@app.route("/")
def home():
    all_movies = db.session.query(Movie).all()

    return render_template("index.html", all_movies=all_movies)


@app.route("/edit_movie/<int:movie_id>", methods=["POST", "GET"])
def edit_movie(movie_id):
    update_form = RateMovieForm()
    if update_form.validate_on_submit():
        new_rating = update_form.rating.data
        new_review = update_form.review.data
        update_movie(movie_id, new_rating, new_review)

        return redirect(url_for('home'))

    return render_template("edit.html", update_form=update_form)


@app.route("/delete_movie/<int:movie_id>")
def delete_movie(movie_id):
    delete(movie_id)

    return redirect(url_for("home"))


@app.route("/add_movie", methods=["POST", "GET"])
def add_movie():
    add_form = AddMovieForm()
    if add_form.validate_on_submit():
        movie_title = add_form.title.data
        search_movies(movie_title)
        movies_data = movies_titles_list()

        return render_template("select.html", movies_data=movies_data)

    return render_template("add.html", add_form=add_form)


@app.route("/add_movie/<int:selection>/<movie_title>", methods=["POST", "GET"])
def select_movie(selection, movie_title):
    movie_details = get_movie_details(selection)

    return render_template("movie.html", movie_title=movie_title, movie_details=movie_details)


if __name__ == '__main__':
    app.run(debug=True)
