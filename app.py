import os
import flask
from flask_cors import CORS
import random
import json
from genius import get_lyrics_link
from spotify import get_access_token, get_song_data
from flask_login import login_user, current_user, LoginManager
from flask_login.utils import login_required
from dotenv import load_dotenv, find_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

load_dotenv(find_dotenv())


app = flask.Flask(__name__, static_folder="./build/static")
CORS(app)
# Point SQLAlchemy to Heroku database
db_url = os.getenv("DATABASE_URL")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
# Gets rid of a warning
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.getenv("APP_SECRET_KEY")

db = SQLAlchemy(app)

# database User and Artist models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))

    def __repr__(self):
        return f"<User {self.username}>"

    def get_username(self):
        return self.username


class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), nullable=False)

    def __repr__(self):
        return f"<Artist {self.artist_id}>"


db.create_all()

# Tells Flask app to look at the results of `npm build` instead of the
# actual files in /templates
bp = flask.Blueprint("bp", __name__, template_folder="./build")


@bp.route("/index")
@login_required
def index():
    # get current user's artists from database
    artists = Artist.query.filter_by(username=current_user.username).all()
    artist_ids = [a.artist_id for a in artists]
    has_artists_saved = len(artist_ids) > 0
    # choose a random artist
    if has_artists_saved:
        artist_id = random.choice(artist_ids)
        # get song data for chosen artist
        access_token = get_access_token()
        (song_name, song_artist, song_image_url, preview_url) = get_song_data(
            artist_id, access_token
        )
        genius_url = get_lyrics_link(song_name)

    else:
        (song_name, song_artist, song_image_url, preview_url, genius_url) = (
            None,
            None,
            None,
            None,
            None,
        )
    # Data to send to client-side javascript
    DATA = {
        "has_artists_saved": has_artists_saved,
        "song_name": song_name,
        "song_artist": song_artist,
        "song_image_url": song_image_url,
        "preview_url": preview_url,
        "genius_url": genius_url,
        "current_user": current_user.username,
        "artist_ids": artist_ids,
    }
    data = json.dumps(DATA)
    return flask.render_template(
        "index.html",
        data=data,
    )


app.register_blueprint(bp)

# login manager stuff
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_name):
    return User.query.get(user_name)


# Routes
@app.route("/signup")
def signup():
    return flask.render_template("signup.html")


@app.route("/signup", methods=["POST"])
def signup_post():
    # Get username and add it to database
    username = flask.request.form.get("username")
    user = User.query.filter_by(username=username).first()
    if user:
        pass
    else:
        user = User(username=username)
        db.session.add(user)
        db.session.commit()

    return flask.redirect(flask.url_for("login"))


@app.route("/login")
def login():
    return flask.render_template("login.html")


@app.route("/login", methods=["POST"])
def login_post():
    # login user
    username = flask.request.form.get("username")
    user = User.query.filter_by(username=username).first()
    if user:
        login_user(user)
        return flask.redirect(flask.url_for("bp.index"))

    else:
        return flask.jsonify({"status": 401, "reason": "Username or Password Error"})


@app.route("/")
def main():
    if current_user.is_authenticated:
        return flask.redirect(flask.url_for("bp.index"))
    return flask.redirect(flask.url_for("login"))


@app.route("/addArtist", methods=["POST"])
def addArtist():
    artist_id = flask.request.json.get("artist_id")

    # check if artist already saved to database
    artist_check = Artist.query.filter_by(
        artist_id=artist_id, username=current_user.username
    ).first()

    if not artist_check:
        try:
            access_token = get_access_token()
            get_song_data(artist_id, access_token)
        except Exception:
            flask.flash("Invalid artist ID entered")
            return flask.redirect(flask.url_for("bp.index"))
        # add artist to database
        username = current_user.username
        db.session.add(Artist(artist_id=artist_id, username=username))
        db.session.commit()
        flask.flash("Artist added. Add another or press save to save changes")
    else:
        flask.flash("You already saved this artist")
    artists = Artist.query.filter_by(username=current_user.username).all()
    artist_ids = [a.artist_id for a in artists]

    return flask.jsonify({"artist_IDs_server": artist_ids})


@app.route("/deleteArtist", methods=["POST"])
def deleteArtist():
    artist_id = flask.request.json.get("artist_id")
    # remove artist from database
    db.session.query(Artist).filter(Artist.artist_id == artist_id).delete()
    db.session.commit()

    artists = Artist.query.filter_by(username=current_user.username).all()
    artist_ids = [a.artist_id for a in artists]
    return flask.jsonify({"artist_IDs_server": artist_ids})


app.run(
    host=os.getenv("IP", "0.0.0.0"),
    port=int(os.getenv("PORT", 8081)),
)
