from flask import Flask, render_template

app = Flask(__name__)

# ... existing routes ...

@app.errorhandler(404)
def page_not_found(error) -> tuple:
    return render_template("404.html"), 404

