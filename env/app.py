from flask import Flask,render_template
app = Flask(__name__)

@app.route("/")
def index():
    return "Ana Sayfa"

@app.route("/about")
def about():
    return "Hakkımda"

@app.route("/about/kerem")
def kerem():
    return "Kerem Hakkında"

if __name__ == "__main__":
    app.run(debug=True)
