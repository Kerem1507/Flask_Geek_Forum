import os
from flask import Flask,render_template,flash,redirect,url_for,session,logging,request,abort
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
from werkzeug.utils import secure_filename

app = Flask(__name__)

#Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Please login to view this page!","danger")
            return redirect(url_for("login"))
    return decorated_function

#Register Form
class RegisterForm(Form):
    name = StringField("Name & Surname", validators = [validators.Length(min = 4, max = 30)])
    username = StringField("Username", validators = [validators.Length(min = 5, max = 35)])
    email = StringField("Email Address", validators = [validators.Email(message="Please enter a valid email address!")])
    password = PasswordField("Password", validators =[
        validators.DataRequired(message = "Please enter a Password..."),
        validators.EqualTo(fieldname = "confirm",message="Please check your Password!")])
    confirm = PasswordField("Verify Your Password")

#Registration
@app.route("/register", methods=["GET","POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()
        flash("Your registration has been successfully done!","success")
        return redirect(url_for("login"))
    
    else:
        return render_template("register.html",form = form)

#Login Form
class LoginForm(Form):
    username = StringField("Username:")
    password = PasswordField("Password:")

#Login
@app.route("/login", methods= ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()
        sorgu = "Select * From users where username = %s"
        result = cursor.execute(sorgu,(username,))
        
        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("You have successfully logged in!","success")
                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("You entered your password incorrectly!","danger")
                return redirect(url_for("login"))

        else:
            flash("There is no user such this!","danger")
            return redirect(url_for("login"))
    
    return render_template("login.html",form = form)

#Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

#Dashboard
@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where author = %s"
    result = cursor.execute(sorgu,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
        return render_template("dashboard.html")

#Posts
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles"
    result = cursor.execute(sorgu)

    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html",articles = articles)
    else:
        return render_template("articles.html")

#Post Form
class ArticleForm(Form):
    title = StringField("Post Title",validators=[validators.Length(min = 5, max = 100)])
    content = TextAreaField("Content",validators=[validators.Length(min = 10)])
    
#Creating Posts
@app.route("/addarticle",methods=["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data
        cursor = mysql.connection.cursor()
        sorgu = "Insert into articles (title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("Your post was successfully created!","success")
        return redirect(url_for("dashboard"))
    return render_template("addarticle.html",form = form)

#Post Details
@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from articles where id = %s"
    result = cursor.execute(sorgu,(id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html",article = article)
    else:
        return render_template("article.html")

#Deleting Posts
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from articles where author = %s and id = %s"
    result = cursor.execute(sorgu,(session["username"],id))

    if result > 0:
        sorgu2 = "Delete from articles where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        flash("Your post has successfully deleted!","warning")
        return redirect(url_for("dashboard"))
        
    else:
        flash("There is no such article or you are not authorized to delete it!","danger")
        return(url_for("index"))

#Editing Posts
@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required
def update(id):
    #GET Request Code
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "Select * from articles where id = %s and author = %s"
        result = cursor.execute(sorgu,(id,session["username"]))

        if result == 0:
            flash("There is no such article or you are not authorized to delete it!","danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form = form)
    else:
        #POST Request Code
        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data
        sorgu2 = "Update articles Set title = %s,content = %s where id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()

        flash("Your post has successfully edited!","success")
        return redirect(url_for("dashboard"))  

#Searching URL
@app.route("/search",methods = ["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        #POST Request Code
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        sorgu = "Select * from articles where title like '%" + keyword +"%'"
        result = cursor.execute(sorgu)

        if result == 0:
            flash("No articles matching the searched word were found!","danger")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()
            return render_template("articles.html",articles = articles)

#Profile Page
@app.route("/profile",methods=["GET","POST"])
@login_required
def profile():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where author = %s"
    result = cursor.execute(sorgu,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("profile.html",articles = articles)
    else:
        return render_template("profile.html")

#Edit Profile Form
class EditForm(Form):
    username = StringField("Username", validators = [validators.Length(min = 5, max = 35)])
    password = PasswordField("Password", validators =[
        validators.DataRequired(message = "Please enter a Password..."),
        validators.EqualTo(fieldname = "confirm",message="Please check your Password!")])
    confirm = PasswordField("Verify Your Password")

#Edit Profile
@app.route("/edit",methods = ["GET","POST"])
@login_required
def edit():
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "Select * From users where username = %s"
        result = cursor.execute(sorgu,(session["username"],))

        if result == 0:
            flash("There is no user with such an id or you are not authorized to do this.","danger")
            return redirect(url_for("index"))
        else:
            user = cursor.fetchone()
            form = EditForm()
            form.username.data = user["username"]
            form.password.data = user["password"]
            return render_template("edit.html", form=form)
    else:
        #POST Request
        form = EditForm(request.form)
        newusername = form.username.data
        newpassword = sha256_crypt.encrypt(form.password.data)

        sorgu2 = "Update users Set username = %s, password = %s where id = %s"
        cursor2 = mysql.connection.cursor()
        cursor2.execute(sorgu2,(newusername,newpassword,id,))
        mysql.connection.commit()
        flash("Changes of your profile have been successfully saved.","success")
        flash("Please log out and login again to see the changes.","warning")
        return redirect(url_for("profile"))

#Upload Files
@app.route("/upload")
def upload():
    return render_template("upload.html")

@app.route("/uploader",methods = ["GET","POST"])
def uploader():
    if request.method == "POST":
        f = request.files["file"]
        f.save(secure_filename(f.filename))
        flash("Your File upoloaded successfully!","success")
        return render_template("profile.html")

app.secret_key = "geekforum"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "geekforum"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
mysql = MySQL(app)

#Index 
@app.route("/")
def index():
    return render_template("index.html")
#About
@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True)