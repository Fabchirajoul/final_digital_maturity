import numpy as np
import io
import csv
import base64
from flask import Flask, request, render_template, redirect, session, url_for
import sqlite3
import bcrypt
import random
import string
import math
from flask import jsonify
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend

app = Flask(__name__)
app.secret_key = 'secret_key'


class User:
    def __init__(self, email, password, name, account_type):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode(
            'utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.account_type = account_type

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))


def create_user_table():
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS User (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            account_type TEXT,
            password TEXT NOT NULL,
            userPhoto BLOB
        )
    ''')
    connection.commit()
    connection.close()


# combined table
def create_combined_table():
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS CombinedTable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            BusinessSector TEXT,
            BusinessFunction TEXT,
            MeasuringElt TEXT,
            Rating INTEGER,
            SUbCategory TEXT,
            AsIsQuestions TEXT,
            ToBeQuestions TEXT,
            MaxRating INTEGER
        )
    ''')
    connection.commit()
    connection.close()


def create_user_submission_record_table():
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS UserSubmissionRecord (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            UniqueCodeUser TEXT,
            BusinessFunction TEXT,  
            MeasuringEltUser TEXT,
            RatingUser INTEGER,
            SUbCategoryUser TEXT,
            AsIsQuestionsUser TEXT,
            AnswersUserAsIs TEXT,
            ToBeQuestionsUser TEXT,
            AnswersUserToBe TEXT,   
            MaxRatingUser INTEGER DEFAULT 5,
            ExpectedCumSum INTEGER,
            UserCumSumAsIs INTEGER,
            UserCumSumToBe INTEGER
        )
    ''')
    connection.commit()
    connection.close()


# Recreate the table to ensure the schema is correct
create_user_submission_record_table()

# TO hold trimmed records


def create_user_submission_trimmed_record_table():
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS UserSubmissionRecordTrimmed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            UniqueCodeUser TEXT,
            BusinessFunction TEXT,  
            MeasuringEltUser TEXT,
            RatingUser INTEGER,
            SUbCategoryUser TEXT,
            AsIsQuestionsUser TEXT,
            AnswersUserAsIs TEXT,
            ToBeQuestionsUser TEXT,
            AnswersUserToBe TEXT,   
            MaxRatingUser INTEGER DEFAULT 5,
            ExpectedCumSum INTEGER,
            UserCumSumAsIs INTEGER,
            UserCumSumToBe INTEGER
        )
    ''')
    connection.commit()
    connection.close()


def create_final_feedback_data():
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS UserSubmittedFeedback (
            UniqueCodeUser TEXT,
            BusinessFunction TEXT,  
            MeasuringEltUser TEXT,
            RatingUser INTEGER,
            SUbCategoryUser TEXT,
            AnswersUserAsIs TEXT,
            AnswersUserToBe TEXT,   
            MaxRatingUser INTEGER DEFAULT 5,
            ExpectedCumSum INTEGER,
            UserCumSumAsIs INTEGER,
            UserCumSumToBe INTEGER,
            PercentageAsIs INTEGER,
            PercentageToBe INTEGER,
            FeedbackAsIs TEXT,
            FeedbackToBe TEXT,
            GrowthRate INTEGER,
            Duration INTEGER
                   
        )
    ''')
    connection.commit()
    connection.close()


create_user_table()
create_combined_table()
create_user_submission_record_table()
create_final_feedback_data()
create_user_submission_trimmed_record_table()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        account_type = request.form['users']
        user_photo = request.files['User_photo']

        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')

        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM User WHERE email=?', (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            connection.close()
            return render_template('register.html', error='User with this email already exists')

        hashed_password = bcrypt.hashpw(password.encode(
            'utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Read the photo data and convert it to binary
        user_photo_data = user_photo.read()

        cursor.execute('INSERT INTO User (name, email, password, account_type, userPhoto) VALUES (?, ?, ?, ?, ?)',
                       (name, email, hashed_password, account_type, user_photo_data))
        connection.commit()
        connection.close()

        return redirect('/login')

    return render_template('register.html')


# Admin register
@app.route('/Adminregister', methods=['GET', 'POST'])
def adminregister():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        account_type = request.form['users']

        if password != confirm_password:
            return render_template('administrator.html', error='Passwords do not match')

        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM User WHERE email=?', (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            connection.close()
            return render_template('administrator.html', error='User with this email already exists')

        hashed_password = bcrypt.hashpw(password.encode(
            'utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute('INSERT INTO User (name, email, password, account_type) VALUES (?, ?, ?, ?)',
                       (name, email, hashed_password, account_type))
        connection.commit()
        connection.close()

        return redirect('/administrator')

    return render_template('administrator.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        account_type = request.form['users']

        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM User WHERE email=?', (email,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[4].encode('utf-8')) and user[3] == account_type:
            session['email'] = user[2]
            if account_type == "Administrator":
                return redirect('/administrator')
            elif account_type == "Business Analyst":
                return redirect('/userAccount')
        else:
            error_message = "Invalid credentials. Please make sure to enter the correct email, password, and account type."
            return render_template('login.html', error=error_message)

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('email', None)
    return render_template('index.html')


@app.route('/userAccount')
def dashboardBusinessAnalyst():
    business_functions_data = {}
    if session.get('email'):
        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM User WHERE email=?', (session['email'],))
        user = cursor.fetchone()
        connection.close()

        # Convert the user photo to a base64 string if it exists
        user_photo_base64 = None
        if user:
            if user[5]:  # Check if the photo column has data
                user_photo_base64 = base64.b64encode(user[5]).decode('utf-8')

        return render_template('userAccount.html', user=user, user_photo_base64=user_photo_base64, business_data=business_functions_data)
    return redirect('/login')


@app.route('/administrator')
def dashboardAdministrator():
    if session.get('email'):
        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM User WHERE email=?', (session['email'],))
        user = cursor.fetchone()
        connection.close()
        return render_template('administrator.html', user=user)

    return redirect('/login')

# Creating the combined all tiers


@app.route('/CombinedTiersForAll', methods=['GET', 'POST'])
def CombinedTiers():
    if request.method == 'POST':
        business_sector_name = request.form['business_sector_name']
        business_function_name = request.form['business_function']
        measuring_element_name = request.form['Measuring_Element']
        rating = request.form['Rating']
        subCategory_name = request.form['subCategory_name']

        # Dynamically generate the as_is_question and to_be_question
        as_is_question = f"Wrt to the 10 best companies incorporating industry 4.0 key enablers making them digitally mature and transformed, how will you best describe your {
            subCategory_name}?"
        to_be_question = f"Wrt to the 10 best companies incorporating industry 4.0 key enablers making them digitally mature and transformed, where would you want to find {
            subCategory_name} in the future?"

        MaxRating = request.form['MaxRating']

        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()
        cursor.execute('''
            INSERT INTO CombinedTable (BusinessSector, BusinessFunction, MeasuringElt, Rating, SUbCategory, AsIsQuestions, ToBeQuestions, MaxRating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (business_sector_name, business_function_name, measuring_element_name, rating, subCategory_name, as_is_question, to_be_question, MaxRating))
        connection.commit()
        connection.close()

        return redirect('/CombinedTiersForAll')

    return render_template('administrator.html')


# Updating the combined tiers
@app.route('/UpdateCombinedTiersForAll', methods=['GET', 'POST'])
def UpdateCombinedTiers():
    if request.method == 'POST':
        # Extract old values from the form
        oldbusiness_sector_name = request.form['oldbusiness_sector_name']
        oldbusiness_function = request.form['oldbusiness_function']
        oldmeasuring_element_name = request.form['oldMeasuring_Element']
        oldrating = request.form['oldRating']
        oldsubCategory_name = request.form['oldsubCategory_name']
        oldMaxRating = request.form['oldMaxRating']

        # Extract new values from the form
        newbusiness_sector_name = request.form['newbusiness_sector_name']
        newbusiness_function = request.form['newbusiness_function']
        newmeasuring_element_name = request.form['newMeasuring_Element']
        newrating = request.form['newRating']
        newsubCategory_name = request.form['newsubCategory_name']
        newMaxRating = request.form['newMaxRating']

        # Connect to the database
        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()

        # Execute the SQL update query
        cursor.execute('''
            UPDATE CombinedTable 
            SET BusinessSector=?, BusinessFunction=?, MeasuringElt=?, Rating=?, SUbCategory=?, MaxRating=?
            WHERE BusinessSector=? AND BusinessFunction=? AND MeasuringElt=? AND Rating=? AND SUbCategory=? AND MaxRating=?
        ''', (newbusiness_sector_name, newbusiness_function, newmeasuring_element_name, newrating, newsubCategory_name, newMaxRating,
              oldbusiness_sector_name, oldbusiness_function, oldmeasuring_element_name, oldrating, oldsubCategory_name, oldMaxRating))

        # Commit changes and close connection
        connection.commit()
        connection.close()

        # Redirect back to administrator page
        return redirect('/administrator')

    return render_template('administrator.html')


# Route to delete a record from CombinedTable


@app.route('/delete_combined_data', methods=['POST'])
def delete_combined_data():
    if request.method == 'POST':
        # Get the ID of the record to delete from the form
        delete_record_id = request.form['record_id']
        try:
            # Delete the record from the database
            connection = sqlite3.connect('database.db')
            cursor = connection.cursor()
            cursor.execute('''
                DELETE FROM CombinedTable
                WHERE id = ?
            ''', (delete_record_id,))
            connection.commit()
            connection.close()

            # Redirect back to the page displaying combined data
            return redirect('/view_combined_data')
        except Exception as e:

            return "Error occurred during deletion: " + str(e)
    else:
        return "Method Not Allowed"
# delete user record


@app.route('/delete_user_data', methods=['POST'])
def delete_user_record_data():
    if request.method == 'POST':
        # Get the ID of the record to delete from the form
        delete_record_user_id = request.form['user_record_id']
        try:
            # Delete the record from the database
            connection = sqlite3.connect('database.db')
            cursor = connection.cursor()
            cursor.execute('''
                DELETE FROM User
                WHERE name = ?
            ''', (delete_record_user_id,))
            connection.commit()
            connection.close()

            # Redirect back to the page displaying combined data
            return redirect('/view_combined_data')
        except Exception as e:

            return "Error occurred during deletion: " + str(e)
    else:
        return "Method Not Allowed"


# Displaying the elements in the databse on the admin side of the panel
@app.route('/view_combined_data', methods=['GET', 'POST'])
def view_combined_data():
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('''
        SELECT id, BusinessSector, BusinessFunction, MeasuringElt, Rating, SUbCategory, AsIsQuestions, ToBeQuestions, MaxRating
        FROM CombinedTable
    ''')
    combined_data = cursor.fetchall()
    connection.close()

    return render_template('administrator.html', combined_data=combined_data)

# Route to display all user account


@app.route('/view_all_user', methods=['GET', 'POST'])
def view_user_account():
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('''
        SELECT name, email, account_type
        FROM User
    ''')
    all_data = cursor.fetchall()
    connection.close()

    return render_template('administrator.html', all_data=all_data)


# uploading csv file to database
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            # Process CSV file and insert into database
            process_csv(file)
            # Redirect to view data
            return redirect(url_for('view_combined_data'))
    return render_template('administrator.html')


def process_csv(csv_file):
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    # Convert file object to text mode
    csv_text = csv_file.stream.read().decode("utf-8")
    csv_data = csv.reader(csv_text.splitlines())

    next(csv_data)  # Skip header row if present
    for row in csv_data:
        if len(row) != 9:
            raise ValueError("CSV file must have exactly 9 columns")

        id, business_sector, business_function, measuring_elt, rating, sub_category, AsIsQuestions, ToBeQuestions, max_rating = row

        # Dynamically generate the as_is_question and to_be_question
        as_is_question = f'Wrt to the 10 best companies incorporating industry 4.0 key enablers making them digitally mature and transformed, how will you best describe your {sub_category}?'
        to_be_question = f'Wrt to the 10 best companies incorporating industry 4.0 key enablers making them digitally mature and transformed, where would you want to find {sub_category} in the future?'

        cursor.execute('''
            INSERT INTO CombinedTable (id, BusinessSector, BusinessFunction, MeasuringElt, Rating, SUbCategory, AsIsQuestions, ToBeQuestions, MaxRating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (id, business_sector, business_function, measuring_elt, rating, sub_category, as_is_question, to_be_question, max_rating))

    connection.commit()
    connection.close()


# Normalizing the data and inserting into a new database  table 















if __name__ == '__main__':
    app.run(debug=True)
