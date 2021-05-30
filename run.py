import os
from functools import wraps
from flask import (
    Flask, render_template, url_for, 
    request, redirect, flash, session, jsonify
)
from flask_pymongo import PyMongo, pymongo
from bson.objectid import ObjectId
from forms import LoginForm, RegisterForm, AddForm, Bootstrap, category_choices
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import BadRequest
from werkzeug.utils import secure_filename

# Pagination imports
from flask_paginate import Pagination, get_page_args

# importing these two from the random string generator to generate random string for image names
import random
import string

# used to add dates to the mongo db collection
from datetime import date

#Import required Image library
from PIL import Image

import json
if os.path.exists("env.py"):
    import env

app = Flask(__name__)

bootstrap = Bootstrap(app)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.config['UPLOAD_FOLDER'] = os.environ.get("UPLOAD_FOLDER")
app.secret_key = os.environ.get("SECRET_KEY")

# Allowed file extensions used by function allowed_files()
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Set up an instance of PyMongo
mongo = PyMongo(app)

# Function to crop image so space is saved and loading time improves
# https://stackoverflow.com/a/20361739
def crop_image(image):
    im = Image.open(image)

    width, height = im.size   # Get dimensions
    left = width/4
    top = height/4
    right = 3 * width/4
    bottom = 3 * height/4
    cropped = im.crop((left, top, right, bottom))

    cropped.save(image,optimize=True,quality=70)

# Resize image
def resize_image(image):
    im = Image.open(image)

    out = im.resize((600, 400), Image.ANTIALIAS)

    out.save(image, optimize=True, quality=80)



def get_ads():
    return mongo.db.ads.find()

@app.errorhandler(BadRequest)
def handle_bad_request(e):
    return render_template("404.html"), 404

app.register_error_handler(404, handle_bad_request)

# Function used to validate file extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Decorators
def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'user' in session:
            return test(*args, **kwargs)
        else:
            flash('You must log in first')
            return redirect(url_for("login"))
    return wrap



# Routes
@app.route("/")
@app.route("/home")
def index():
    return render_template("index.html")


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=session['user'])    


@app.route("/view/", methods=["GET", "POST"])
@app.route("/view/<category>", methods=["GET", "POST"])
def view(category=None):

    ad_data = mongo.db.ads.find()

    results = [] # results for category
    list_split = [] # results for all items, pagination soltution

    if category is not None:
        for i in ad_data:
            if category == i["category"]:
                results.append(i)
        
        return render_template("view.html", data=results)
    
    return render_template("view.html", data=ad_data)



@app.route("/advert/<ad_id>", methods=["POST", "GET"])
@app.route("/advert/", methods=["POST", "GET"])
def advert(ad_id):
    ad = mongo.db.ads.find_one({"_id": ObjectId(ad_id)})

    return render_template("advert.html", ad=ad)




@app.route("/paginate")
def paginate():
    page, per_page, offset = get_page_args(page_parameter='page',
                                           per_page_parameter='per_page')
    total = get_ads().count()
    pagination_ads = get_ads()
    pagination = Pagination(page=page, per_page=per_page, total=total,
                            css_framework='bootstrap4')
    return render_template('paginate.html',
                           ads=pagination_ads,
                           page=page,
                           per_page=per_page,
                           pagination=pagination,
                           )


# TODO: Validate file names so users can't upload the same file twice
# Store date to mongoDB as well as filename and location
@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    form = AddForm()

    # get today's date
    today = date.today()

    # generationg a random string so files are never the same name
    output_string = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(10))

    if form.validate_on_submit():
        #print(request.form)

        # File upload access through request
        fl = request.files['image_upload']

        # Check is file exists and if extension is allowed
        if fl and allowed_file(fl.filename):           
            # if filename exists then we want to keep going
            filename = output_string + "-" + secure_filename(fl.filename)
            #filename_original = output_string + "-original-" + secure_filename(fl.filename)

            # store both the cropped and the original version
            fl.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            #fl.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_original))

            # store both the cropped and the original version
            resize_image(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            #resize_image(os.path.join(app.config['UPLOAD_FOLDER'], filename_original))

            form_data = {
                "name"    : session['name'],
                "user_id" : session["user_id"],
                "phone" : request.form.get('phone'),
                "house_number" : request.form.get('house_number'),
                "category_one" : request.form.get('category_one'),
                "category_two" : request.form.get('category_two'),
                "description" : request.form.get('description'),
                "delivery" : request.form.get('delivery'),
                "filename" : filename,
                "offer" : request.form.get('offer'),
                "price" : request.form.get('price'),
                "date"  : today.strftime('%Y-%m-%d'),
                "is_sponsored" : False,
                "is_approved" : False # initially, all ads will be hidden and approval needed
            }

            print(form_data)

            mongo.db.ads.insert_one(form_data)

            flash('Obrigado por criar um anuncio, ele sera revisado em breve por um dos moderadores')

            return redirect(url_for("profile"))

        else:
            flash("Essa imagem nao e valida!")
            return redirect(url_for("add"))


    return render_template("add_item.html", form=form)



@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    data = mongo.db.ads.find({'is_approved' : False})
    
    if session["is_admin"] and data.count() > 0:
        print(data)
        return render_template("admin.html", data=data)
    elif session["is_admin"] and data.count() == 0:
        return render_template("admin.html", data=0)

    return render_template("profile.html")



@app.route("/approve/", methods=["POST", "GET"])
@app.route("/approve/<id>", methods=["POST", "GET"])
def approve(id):
    #item = mongo.db.ads.find_one({"_id": ObjectId(id)})
    if session["is_admin"] and id:
        
        filter = { "_id" : ObjectId(id) }

        newvalues = { "$set": { "is_approved": True } } 

        mongo.db.ads.update_one(filter, newvalues) 

        flash("O Item foi aprovado com successo!")
        return render_template("admin.html")


    return render_template("profile.html")

@app.route("/reject", methods=["POST", "GET"])
def reject():

    if session["is_admin"]:
        pass
        # use the entry _id to delete the post

    return render_template("profile.html")

@app.route("/user/", methods=["GET", "POST"])
@app.route("/user/<user_id>", methods=["GET", "POST"])
def user(user_id):
    print(user_id)
    if session["is_admin"]:

        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})

        return render_template("user.html", user=user)

    return render_template("profile.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if 'user' in session:
        flash('You are already logged in!')
        return redirect(url_for("profile"))

    if form.validate_on_submit():
        users = mongo.db.users
        login_user = users.find_one({'email' : request.form.get("email").lower()})

        if login_user:
            pw_hash = check_password_hash(login_user["password"], request.form.get("password"))
            
            if pw_hash and not login_user["is_banned"]:

                session.clear()
                session["user"] = request.form.get("email")
                session["is_admin"] = login_user["is_admin"] # Admin has to be set directly in mongo db
                session["user_id"] = str(login_user['_id'])
                session["is_banned"] = login_user['is_banned']
                session["name"] = login_user['name']
                
                flash("Seja Bem-Vindo!")
                return redirect(url_for("profile"))

            flash("Parece que sua conta foi desativada, por favor entre em contato com o admin do site")
            return redirect(url_for("login"))

        else:
            flash("Tem alguma coisa errada, entre em contato com o admin do site")
            return redirect(url_for("login"))

    return render_template("login.html", form=form)




@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if 'user' in session:
        # redirect to profile page as user is logged in
        return redirect(url_for("profile"))

    if form.validate_on_submit():
        # check if username exists in mongodb
        existing_user = mongo.db.users.find_one(
            {"email": request.form.get("email").lower()})

        # display flash message if user already exists
        if existing_user:
            flash("Desculpa, tem outra pessoa usando esse email!")
            return redirect(url_for("register"))
        else:
            register = {
                "email": request.form.get("email"),
                "name": request.form.get("name"),
                "password" : generate_password_hash(request.form.get("password")),
                "is_admin" : False,
                "is_banned" : False
            }

            mongo.db.users.insert_one(register)

            # call the db to get the user again and get user id which has been generated
            user = mongo.db.users.find_one({"email": session["user"]})

            session["user"] = request.form.get("email")
            session["name"] = request.form.get("name")
            session["user_id"] = str(user["_id"])
            flash("Obrigado por registrar no nosso site")
            return redirect(url_for("profile"))

    return render_template("register.html", form=form)


@app.route("/logout")
@login_required
def logout():
    # remove user from session cookie
    session.pop("user")
    session.pop("is_admin", None)
    session.pop("user_id", None)
    session.pop("is_banned", None)
    
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(
        host=os.environ.get("IP"),
        port=int(os.environ.get("PORT")),
        debug=True
    )