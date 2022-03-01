import json
from flask import Flask,render_template, request, jsonify, url_for,Response, redirect,flash
from flask_cors import cross_origin
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from datetime import datetime
from wtforms.widgets import TextArea
from flask_migrate import Migrate
from sqlite3 import dbapi2 as sqlite



#import matplotlib.pyplot as plt
#import xlwt
# need to install xlrd and openpyxl to use read_excel function in pandas
# pandas dataframe interpolate() function/ The interpolate() function is used to interpolate values according to different methods.
#
# Please note that only method='linear' is supported for DataFrame/Series with a MultiIndex
import os
import csv
import shutil
app = Flask(__name__)
# add database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

# secret key
app.config['SECRET_KEY'] = "my super secret key that no one"
#initialise database
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# create model for db
class Users(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(200), nullable = False)
    email = db.Column(db.String(120), nullable = False, unique = True)
    date_added = db.Column(db.DateTime, default = datetime.utcnow)
    posts = db.relationship('Posts', backref = 'author', lazy = True)
    # create a string
    def __repr__(self):
        return f"User('{self.name}', '{self.email}','{self.date_added}')"
#CREATE a Blog post model
class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
#    names = db.Column(db.String(200), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"

# CREATE FORM CLASS
class UserForm(FlaskForm):
    name = StringField("Name", validators= [DataRequired()])
    email = StringField("Email", validators= [DataRequired()])
    submit = SubmitField("Submit")

class BlogForm(FlaskForm):
    names = StringField("Name", validators= [DataRequired()])
    title = StringField("Title", validators=[DataRequired()])

    content = StringField("Content", validators=[DataRequired()], widget= TextArea())

    submit = SubmitField("Submit")

@app.route('/add_user', methods = ['GET', 'POST'])
def add_user():
    name = None
    form = UserForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email = form.email.data).first()
        if user is None:
            user= Users(name=form.name.data,email = form.email.data)
            db.session.add(user)
            db.session.commit()
        name = form.name.data
        form.name.data = ''
        form.email.data = ''
        flash("User Added Successfully")
    our_users = Users.query.order_by(Users.date_added)
    return render_template('add_user.html', form=form, name = name, our_users = our_users)

##add blog POST MODEL######


## add post form ###
@app.route('/add_blog', methods = ['GET', 'POST'])
def add_blog():
    names = None
    form = BlogForm()
    if form.validate_on_submit():
       # poster = current_user.id
        post = Posts(title= form.title.data, content = form.content.data)
        #clearing the form ##
        form.title.data = ''
        form.content.data = ''
        form.names.data = ''

        # add data to database #
        db.session.add(post)
        db.session.commit()
        flash("Blog post submitted successfully ")

    return render_template('add_blog.html', form=form)
@app.route('/')
@app.route('/home')
@cross_origin()
def home_page():

    return render_template('index3.html')

@app.route('/blog')
def about():
    title= "About time point screening"
    return render_template('blog.html', title=title)

@app.route('/clear_data',methods=['GET', 'POST'])
def clear_data():
    filepath = ('Static\Input.xlsx')
    filepath1 = ('Static\Temp.xlsx')
    if os.path.isfile(filepath):
        os.remove(filepath)
        comment =" file has been cleared"
    if os.path.isfile(filepath1):
        os.remove(filepath1)
        comment = "  Temp File has been cleared"
    else:
        comment = "     !!!! No file Exists"
    return render_template('download.html', clear_data=comment)

@app.route('/data', methods=['GET', 'POST'])
def data():
    if request.method == 'POST':
        try:

            #file = request.form['upload-file']
            file = request.files['upload-file']
            if not os.path.isdir('Static'):
                os.mkdir('Static')

            filepath1 = os.path.join('Static', file.filename)
            print(filepath1)
            if os.path.isfile(filepath1):
                os.remove(filepath1)
                print("source file is copied to dataframe and deleted")
            file.save(filepath1)
            #dest = os.path.join('Static' + 'worksheet.xlsx' )
            #os.rename(filepath1,dest)
            filepath = ('Static\working_data.xlsx')
            #data1 = pd.read_excel(file)

            #data1 = pd.read_excel(filepath1,sheet_name='Temp vs Time', skiprows = 3)
            #temp_data= pd.read_excel(filepath1,sheet_name='Temperature difference', skiprows = 1)
            pressure_data = pd.read_excel(filepath1, sheet_name='Input',index_col='Time', skiprows=1)
            pressure_data = pressure_data[pressure_data.filter(regex='^(?!Unnamed)').columns]
            # Remove the 1st row with units from the table
            pressure_data = pressure_data.drop(pressure_data.index[[0]])
            data1 = pressure_data
            data1.to_excel('Static\Temp.xlsx')
            coll = pressure_data.columns.to_list()
            for col in pressure_data:
                pressure_data[col] = pd.to_numeric(pressure_data[col], errors='coerce')
            data22 = pd.read_excel(filepath1, sheet_name='Interpolate_data', index_col='Time')
            # keep the data to be interpolated in sheet named Interpolate _data
            # make sure for data22 the excel has file name Interpolate_data and has 1st column with "Time"
            data22 = data22[data22.filter(regex='^(?!Unnamed)').columns]
            aa = data22.index.values
            ser= pd.Series(aa)
            #aa = pd.to_numeric(aa)
            # creating a blank dataframe with columns from the inputs and row values to be interpolated
            new = pd.DataFrame(columns=coll, index=ser)
            # combining two dataframe into one dataframe to find the missing value by interpolation with index method.
            concatenated = pd.concat([pressure_data , new])
            con = concatenated.interpolate(method='index')
            # save the interpolated dataframe to excel file.
            #con.to_excel('Static\Interpolated_file.xlsx')
            os.remove(filepath1)
            print(con.shape)
            return Response(
                con.to_csv(),
                mimetype="text/csv",
                headers={"Content-disposition":
                             "attachment; filename=Interpolated file.csv"})
        except Exception as e:
            print('The Exception message is: ', e)
            return 'something is wrong in Interpolate module, check for input file'


if __name__   ==   '__main__':
    app.run(debug=True)