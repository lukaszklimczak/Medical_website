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

@app.route('/contact')
def contact():
    return render_template("contact.html")




if __name__ == "__main__":
    app.run(debug=True)
