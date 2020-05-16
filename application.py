from flask import Flask,render_template,flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField , validators
from passlib.hash import sha256_crypt
from functools import wraps

from data import Articles


app=Flask(__name__)
#Setting up secret key
app.secret_key='secret123456'


#Config MySQL
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='Gurudev#123'
app.config['MYSQL_DB']='myflaskapp'
app.config['MYSQL_CURSORCLASS']='DictCursor'

#init MySQL
mysql=MySQL(app)


# articles=Articles()

#Index
@app.route("/")
def index():
    return render_template("home.html")

#About
@app.route("/about")
def about():
    return render_template("about.html")

# All articles
@app.route("/articles")
def articles():
    # articles=Articles()
    # return render_template("articles.html",articles=articles)

    #Create cursor
    cur=mysql.connection.cursor()

    #Get articles
    result=cur.execute("SELECT * FROM articles")

    articles=cur.fetchall()

    if result>0:
        return render_template("articles.html",articles=articles)
    else:
        msg='No articles found'
        return render_template("articles.html",msg=msg)
    # Close connection
    cur.close()


#Single article
@app.route("/article/<string:id>")
def article(id):
    #Create cursor
    cur=mysql.connection.cursor()

    #Get article
    result=cur.execute("SELECT * FROM articles WHERE id=%s",[id])

    article=cur.fetchone()
    return render_template("article.html",article=article)


#Registration form class created
class RegisterForm(Form):
    name=StringField("Name",[validators.Length(min=1,max=50)])
    username=StringField("Username",[validators.Length(min=4,max=50)])
    email=StringField("Email",[validators.Length(min=6,max=50)])
    password=PasswordField("Password",[
        validators.DataRequired(),
        validators.EqualTo("confirm",message="Passwords do not match")
    ])
    confirm=PasswordField("Confirm Password")


#User Register route
@app.route("/register",methods=["POST","GET"])
def register():
    form=RegisterForm(request.form)
    if(request.method=="POST" and form.validate()):
        name=form.name.data
        email=form.email.data
        username=form.username.data
        password=sha256_crypt.encrypt(str(form.password.data))

        #create cursor
        cur=mysql.connection.cursor()
        #cursor is acting as bridge between the data and the mysql database

        #Execute query
        cur.execute("INSERT INTO users(name,email,username,password) VALUES(%s, %s, %s, %s)", (name,email,username,password))


        #Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('You are now registered and can log in','success')

        redirect(url_for('index'))

    return render_template("register.html",form=form)

# User login route
@app.route("/login",methods=['POST','GET'])
def login():
    if request.method=='POST':
        #Get Form Fields
        username=request.form['username']
        password_candidate=request.form['password']
        type=request.form['type']
        #Create cursor
        cur=mysql.connection.cursor()

        #Get user by Username
        result=cur.execute("SELECT * FROM users WHERE username=%s",[username])

        if result>0 and type=="Patient":
            #Get stored hash
            data=cur.fetchone()
            password=data['password']
            #Compare passwords
            if sha256_crypt.verify(password_candidate,password):
                #Passed and session created
                session['logged_in']=True
                session['username']=username
                flash('You are now logged in.','success')
                return redirect(url_for('dashboard_patient'))
            else:
                error="Invalid login. Please enter correct password."
                return render_template('login.html',error=error)
            #Close connection
            cur.close()

        elif result>0 and type=="Doctor":
            #Get stored hash
            data=cur.fetchone()
            password=data['password']
            #Compare passwords
            if sha256_crypt.verify(password_candidate,password):
                #Passed and session created
                session['logged_in']=True
                session['username']=username
                flash('You are now logged in.','success')
                return redirect(url_for('dashboard_doctor'))
            else:
                error="Invalid login. Please enter correct password."
                return render_template('login.html',error=error)
            #Close connection
            cur.close()
        else:
            error="Username not found. Please register first."
            return render_template('login.html',error=error)

    return render_template('login.html')


#Check if user is logged in(using flask-decorator)
def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            flash('Unauthorized, Please login.','danger')
            return redirect(url_for('login'))
    return wrap


#Logout
@app.route("/logout")
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out.','success')
    return redirect(url_for('login'))


# Dashboard route
@app.route("/dashboard_patient")
@is_logged_in
def dashboard_patient():
    #Create cursor
    cur=mysql.connection.cursor()

    #Get articles
    result=cur.execute("SELECT * FROM articles")

    articles=cur.fetchall()

    if result>0:
        return render_template("dashboard_patient.html",articles=articles)
    else:
        msg='No articles found'
        return render_template("dashboard_patient.html",msg=msg)
    # Close connection
    cur.close()

# Dashboard route
@app.route("/dashboard_doctor")
@is_logged_in
def dashboard_doctor():
    #Create cursor
    cur=mysql.connection.cursor()

    #Get articles
    result=cur.execute("SELECT * FROM articles")

    articles=cur.fetchall()

    if result>0:
        return render_template("dashboard_doctor.html",articles=articles)
    else:
        msg='No articles found'
        return render_template("dashboard_doctor.html",msg=msg)
    # Close connection
    cur.close()





#Article form class
class ArticleForm(Form):
    title=StringField("Title",[validators.Length(min=1,max=200)])
    body=TextAreaField("Body",[validators.Length(min=30)])

# Add article route
@app.route("/add_article",methods=["GET","POST"])
@is_logged_in
def add_article():
    form=ArticleForm(request.form)
    if request.method=='POST' and form.validate():
        title=form.title.data
        body=form.body.data

        # Create cursor
        cur=mysql.connection.cursor()

        #Execute
        cur.execute("INSERT INTO articles(title,body,author) VALUES(%s,%s,%s)", (title,body,session['username']))

        #Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Article created','success')
        return redirect(url_for('dashboard_patient'))

    return render_template('add_article.html',form=form)



# Edit article route
@app.route("/edit_article/<string:id>",methods=["GET","POST"])
@is_logged_in
def edit_article(id):
    #Create cursor
    cur=mysql.connection.cursor()

    #Get the article
    result=cur.execute("SELECT * FROM articles WHERE id=%s",[id])

    article=cur.fetchone()
    cur.close()

    #Get Form
    form=ArticleForm(request.form)

    #Populate article form
    form.title.data=article['title']
    form.body.data=article['body']

    if request.method=='POST' and form.validate():
        title=request.form['title']
        body=request.form['body']

        # Create cursor
        cur=mysql.connection.cursor()

        #Execute
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s", (title,body,id))

        #Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Article updated','success')
        return redirect(url_for('dashboard_doctor'))

    return render_template('edit_article.html',form=form)


#Delete article
@app.route("/delete_article/<string:id>",methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create cursor
    cur=mysql.connection.cursor()

    #Execute
    cur.execute("DELETE from articles WHERE id=%s",[id])

    #Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Article deleted','success')
    return redirect(url_for('dashboard_doctor'))



if __name__=='__main__':
    app.debug=True
    app.run()
