from flask import Flask
from flask import render_template
from flask import request
from model import WatchedTerm
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

app = Flask(__name__)

engine = create_engine("sqlite:///lol.sqlite")

@app.route("/")
def home():
    with Session(engine) as session:
        terms = session.query(WatchedTerm).all()
        return render_template("index.html", terms=terms)

@app.route("/new", methods=["POST"])
def new_term():
    url = request.form.get("url")
    max_price = request.form.get("max_price")
    max_likes = request.form.get("max_likes")

    if url is None:
        return "No url provided"

    try:
        max_likes = int(max_likes)
        max_price = float(max_price)
    except:
        return "Invalid data"

    session = Session(engine)
    term = WatchedTerm(url=url, max_price=max_price, max_likes=max_likes)
    session.add_all([term])
    session.commit()
    session.close()
    return ""


