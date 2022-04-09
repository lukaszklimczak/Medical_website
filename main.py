from flask import Flask, render_template, url_for, redirect, flash, abort
from flask_bootstrap import Bootstrap
# from flask_fontawesome import FontAwesome
from datetime import date


app = Flask(__name__)
Bootstrap(app)
# fa = FontAwesome(app)


@app.route("/")
def about():
    return render_template("about.html")


@app.route('/online-therapy')
def online_therapy():
    return render_template("online-therapy.html")


@app.route('/mobile-advice')
def mobile_advice():
    return render_template("mobile-advice.html")


@app.route('/couple-therapy')
def couple_therapy():
    return render_template("couple-therapy.html")


@app.route('/phobies')
def phobies():
    return render_template("phobies.html")


@app.route('/stress')
def stress():
    return render_template("stress.html")


@app.route('/depression')
def depression():
    return render_template("depression.html")


@app.route('/contact')
def contact():
    return render_template("contact.html")




if __name__ == "__main__":
    app.run(debug=True)
