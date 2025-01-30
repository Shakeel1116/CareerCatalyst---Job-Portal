import csv
from random import randint
from grpc import insecure_channel
from sklearn.preprocessing import LabelEncoder
from flask import Flask, render_template, request, redirect, send_file, send_from_directory, url_for, flash, session
import numpy as np
import mysql.connector
import os
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import pickle

from sklearn.metrics.pairwise import cosine_similarity


app = Flask(__name__)
app.config['SECRET_KEY'] = 'cnnnnnnnnnnn'
app.config['uploadfolder'] = "static/"
mydb = mysql.connector.connect(host="localhost", user="root", passwd="",port=3306, database="job_mapper")
cursor = mydb.cursor()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/seeker_skills')
def seeker_skills():
    return render_template('seeker_skills.html')

import re

@app.route('/signupback', methods=['POST', 'GET'])
def registration():
    if request.method == 'POST':
        # Retrieve form data
        form_data = request.form.to_dict()  # Store all form inputs
        name = form_data.get('name', '')
        email = form_data.get('email', '')
        pwd = form_data.get('pwd', '')
        cpwd = form_data.get('cpwd', '')
        pno = form_data.get('pno', '')
        addr = form_data.get('addr', '')
        state = form_data.get('state', '')
        gender = form_data.get('gender', '')
        age = form_data.get('age', '')

        # Validate age
        try:
            age = int(age)
            if not (18 <= age <= 70):
                flash("Age must be between 18 and 70.", "info")
                return render_template('signup.html', form_data=form_data)
        except ValueError:
            flash("Invalid age. Please enter a number.", "danger")
            return render_template('signup.html', form_data=form_data)

        # File upload handling
        file = request.files.get('filen')
        if not file or file.filename == '':
            flash("No file selected. Please upload a profile picture.", "danger")
            return render_template('signup.html', form_data=form_data)

        file_name = file.filename
        allowed_extensions = {'jpg', 'jpeg', 'png'}
        file_extension = os.path.splitext(file_name)[1][1:].lower()
        if file_extension not in allowed_extensions:
            flash("Invalid file type. Only JPG, JPEG, and PNG files are allowed.", "danger")
            return render_template('signup.html', form_data=form_data)

        # Save the file
        path = os.path.join(app.config['uploadfolder'], 'profiles', file_name)
        file.save(path)

        # Validation for name (only alphabets allowed)
        if not re.fullmatch(r'[A-Za-z ]+', name):
            flash("Name should only contain alphabets and spaces.", "danger")
            return render_template('signup.html', form_data=form_data)

        # Validation for phone number (10 digits only)
        if not re.fullmatch(r'\d{10}', pno):
            flash("Phone number should contain exactly 10 digits.", "danger")
            return render_template('signup.html', form_data=form_data)

        # Validation for password match
        if pwd != cpwd:
            flash("Password and confirm password do not match.", "danger")
            return render_template('signup.html', form_data=form_data)

        # Check if email is already registered
        voters = pd.read_sql_query('SELECT * FROM job_seeker', mydb)
        all_emails = voters.email.values
        if email in all_emails:
            flash("Email is already registered.", "warning")
            return render_template('signup.html', form_data=form_data)

        # Insert into the database
        sql = 'INSERT INTO job_seeker (name, email, pwd, pno, gender, age, addr, state, pgoto) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
        cur = mydb.cursor()
        cur.execute(sql, (name, email, pwd, pno, gender, age, addr, state, path))
        mydb.commit()
        cur.close()
        flash("Account created successfully", "success")
        return redirect(url_for("seeker_skills"))

    return render_template('signup.html')



@app.route('/seeker_skills', methods=['POST', 'GET'])
def seeker_skills_view():
    if request.method == 'POST':
        # Retrieve the data from the form
        name = request.form['name']
        email = request.form['email']
        #role = request.form['role']
        skills = request.form['skills']
        expected_salary = request.form['expectedsalary']
        experience = request.form['experience']

        # SQL query to insert the seeker skills into the database
        sql = '''INSERT INTO seeker_skills (name, email, skills, expectedsalary, experience) 
                 VALUES (%s, %s, %s, %s, %s)'''
        cur = mydb.cursor()
        cur.execute(sql, (name, email, skills, expected_salary, experience))
        mydb.commit()
        cur.close()

        # Flash success message
        flash("Skills and experience updated successfully", "success")
        return redirect(url_for("signin"))  # Redirect to a relevant page after successful insertion
    return render_template('seeker_skills.html')  # Render the skills input page



@app.route('/signin')
def signin():
    return render_template('signin.html')


@app.route('/signinback', methods=['POST', 'GET'])
def signinback():
    if request.method == 'POST':
        username = request.form['email']
        password1 = request.form['pwd']

        sql = "select * from job_seeker where email='%s' and pwd='%s' " % (username, password1)
        x = cursor.execute(sql)
        results = cursor.fetchall()
        print(type(results))
        if not results:
            flash("Invalid Email / Password", "danger")
            return render_template('signin.html')
        else:
            # session['cid'] = username
            if len(results) > 0:
                session['name'] = results[0][1]
                session['email'] = results[0][2]
                sql = "select * from job_seeker where email='" + username + "'"
                x = pd.read_sql_query(sql, mydb)
                print(x)
                x = x.drop(['id'], axis=1)
                flash("Welcome ", "success")
                print("==============")
                image = results[0][-2]
                return render_template('job_seekerhome.html', msg=results[0][1], image=image, row_val=x.values.tolist())
    return render_template('signin.html')


@app.route('/signinback1', methods=['POST', 'GET'])
def signinback1():
    if request.method == 'POST':
        username = request.form['email']
        password1 = request.form['pwd']

        sql = "select * from employee where email='%s' and pwd='%s' " % (username, password1)
        x = cursor.execute(sql)
        results = cursor.fetchall()
        print(type(results))
        if not results:
            flash("Invalid Email / Password", "danger")
            return render_template('signin.html')
        else:
            # session['cid'] = username
            if len(results) > 0:
                session['name'] = results[0][1]
                session['email'] = results[0][2]
                session['cname'] = results[0][4]
                sql = "select * from employee where email='" + username + "'"
                x = pd.read_sql_query(sql, mydb)
                print(x)
                x = x.drop(['id'], axis=1)
                flash("Welcome ", "success")
                print("==============")
                image = results[0][-1]
                return render_template('emphome.html', msg=results[0][1], image=image, row_val=x.values.tolist())
                              
    return render_template('signin1.html')


@app.route('/signup1')
def signup1():
    return render_template('signup1.html')


@app.route('/signupback1', methods=['POST', 'GET'])
def signupback1():
    if request.method == 'POST':
        # Retrieve form data and store it in a dictionary
        form_data = request.form.to_dict()  # Store all form inputs
        name = form_data.get('name', '')
        email = form_data.get('email', '')
        pwd = form_data.get('pwd', '')
        cpwd = form_data.get('cpwd', '')
        pno = form_data.get('pno', '')
        cname = form_data.get('cname', '')
        roll = form_data.get('roll', '')
        addr = form_data.get('addr', '')
        state = form_data.get('state', '')
        gender = form_data.get('gender', '')
        age = form_data.get('age', '')

        # Validate age
        try:
            age = int(age)
            if not (18 <= age <= 70):
                flash("Age must be between 18 and 70.", "info")
                return render_template('signup1.html', form_data=form_data)
        except ValueError:
            flash("Invalid age. Please enter a number.", "danger")
            return render_template('signup1.html', form_data=form_data)

        # File upload handling
        file = request.files.get('filen')
        file_name = file.filename
        if not file:
            flash("No file selected. Please upload a profile picture.", "danger")
            return render_template('signup1.html', form_data=form_data)
        allowed_extensions = {'jpg', 'jpeg', 'png'}
        if not file_name.lower().endswith(tuple(allowed_extensions)):
            flash("Invalid file type. Only JPG, JPEG, and PNG files are allowed.", "danger")
            return render_template('signup1.html', form_data=form_data)
        

        # Save the file
        path = os.path.join(app.config['uploadfolder'], 'profiles', file_name)
        file.save(path)

        # Validation for name (only alphabets allowed)
        if not re.fullmatch(r'[A-Za-z ]+', name):
            flash("Name should only contain alphabets and spaces.", "danger")
            return render_template('signup1.html', form_data=form_data)

        # Validation for phone number (10 digits only)
        if not re.fullmatch(r'\d{10}', pno):
            flash("Phone number should contain exactly 10 digits.", "danger")
            return render_template('signup1.html', form_data=form_data)

        # Validation for password match
        if pwd != cpwd:
            flash("Password and confirm password do not match.", "danger")
            return render_template('signup1.html', form_data=form_data)

        # Check if email is already registered
        voters = pd.read_sql_query('SELECT * FROM employee', mydb)
        all_emails = voters.email.values
        if email in all_emails:
            flash("Email is already registered.", "warning")
            return render_template('signup1.html', form_data=form_data)

        # Insert into the database
        sql = 'INSERT INTO employee (name, email, pwd, cname, roll, pno , gender, age, addr, state, photo) VALUES (%s,%s, %s, %s, %s, %s, %s, %s,%s,%s,%s)'
        cur = mydb.cursor()
        cur.execute(sql, (name, email, pwd, cname, roll, pno , gender, age, addr, state, path))
        mydb.commit()
        cur.close()

        flash("Account created successfully", "success")

        # Redirect to the signin page after successful registration
        return redirect(url_for("signin1"))

    # If GET request is made, render the signup page with an empty form
    return render_template('signup1.html', form_data={})


@app.route("/signinback2", methods=["POST", "GET"])
def signinback2():
    if request.method == "POST":
        email = request.form['email']
        pwd = request.form['pwd']
        if email == 'admin' and pwd == 'admin':
            flash("Welcome Admin", "success")
            return render_template('adminhome.html')
        else:
            flash("Invalid Credentials Please Try Again", "warning")
            return render_template('signin2.html')
    return render_template("signin1.html")


@app.route('/upload')
def upload():
    return render_template("upload.html")


@app.route('/signin1home')
def signin1home():
    return render_template("signin1home.html")


@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if request.method == "POST":
        file = request.files.get('f1')  # Get the file from the request
        if not file:
            flash("No file selected. Please upload a file.", "danger")
            return render_template('upload.html')

        file_name = file.filename
        allowed_extensions = {'txt', 'docx', 'pdf'}
        
        # Check if the file has a valid extension
        if not file_name.lower().endswith(tuple(allowed_extensions)):
            flash("Invalid file type. Only txt, docx, and pdf files are allowed.", "danger")
            return render_template('upload.html')

        # Define the path to save the file
        upload_folder = os.path.join(app.config['uploadfolder'], 'resumes')
        os.makedirs(upload_folder, exist_ok=True)  # Create directory if it doesn't exist
        file_path = os.path.join(upload_folder, file_name)

        # Save the file
        file.save(file_path)
        
        # Use placeholders for the query to prevent SQL injection
        sql = "UPDATE job_seeker SET resume=%s WHERE email=%s"
        # Use a tuple for the parameters
        cursor.execute(sql, (file_path, session['email']))
        mydb.commit()

        flash("Resume uploaded successfully!", "success")
        return redirect(url_for("search"))



@app.route('/signin1')
def signin1():
    return render_template('signin1.html')


@app.route('/signin2')
def signin2():
    return render_template('signin2.html')


@app.route('/forgot')
def forgot():
    return render_template('forgot.html')


@app.route('/forgetback', methods=['POST', 'GET'])
def forgetback():
    if request.method == "POST":
        email = request.form['email']
        sql = "select count(*),name,pwd from employee where email='%s'" % (email)
        x = pd.read_sql_query(sql, mydb)
        count = x.values[0][0]
        pwd = x.values[0][2]
        name = x.values[0][1]
        if count == 0:
            
            return render_template('forgot.html')
        else:
            msg = 'This your password :  '
            t = 'Regards,'
            t1 = 'Job Mapper Services.'
            mail_content = 'Dear ' + name + ',' + '\n' + msg + pwd + '\n' + '\n' + t + '\n' + t1
            sender_address = ''
            sender_pass = ''
            receiver_address = email
            message = MIMEMultipart()
            message['From'] = sender_address
            message['To'] = receiver_address
            message['Subject'] = 'Online Job Mapper Services'
            message.attach(MIMEText(mail_content, 'plain'))
            ses = smtplib.SMTP('smtp.gmail.com', 587)
            ses.starttls()
            ses.login(sender_address, sender_pass)
            text = message.as_string()
            ses.sendmail(sender_address, receiver_address, text)
            ses.quit()
            flash("Password sent to your mail ", "success")
            return render_template("signin1.html")

    return render_template('forgot.html')


@app.route('/forgot1')
def forgot1():
    return render_template('forgot.html')


@app.route('/forgetback1', methods=['POST', 'GET'])
def forgetback1():
    if request.method == "POST":
        email = request.form['email']
        sql = "select count(*),name,pwd from job_seeker where email='%s'" % (email)
        x = pd.read_sql_query(sql, mydb)
        count = x.values[0][0]
        pwd = x.values[0][2]
        name = x.values[0][1]
        if count == 0:
           
            return render_template('forgot.html')
        else:
            msg = 'This your password : '
            t = 'Regards,'
            t1 = 'Job Mapper Services.'
            mail_content = 'Dear ' + name + ',' + '\n' + msg + pwd + '\n' + '\n' + t + '\n' + t1
            sender_address = ''
            sender_pass = ''
            receiver_address = email
            message = MIMEMultipart()
            message['From'] = sender_address
            message['To'] = receiver_address
            message['Subject'] = 'Online Job Mapper Services'
            message.attach(MIMEText(mail_content, 'plain'))
            ses = smtplib.SMTP('smtp.gmail.com', 587)
            ses.starttls()
            ses.login(sender_address, sender_pass)
            text = message.as_string()
            ses.sendmail(sender_address, receiver_address, text)
            ses.quit()
            flash("Password sent to your mail ", "success")
            return render_template("signin1.html")

    return render_template('forgot.html')


@app.route('/adminhome')
def adminhome():
    return render_template('adminhome.html')


@app.route('/view_job_seekers')
def view_job_seekers():
    sql = "SELECT * FROM job_seeker"
    cursor.execute(sql)  # No need for the second argument
    data = cursor.fetchall()
    return render_template("view_job_seekers.html", data=data)

@app.route('/view_emlpyers')
def view_emlpyers():
    sql = "SELECT * FROM employee"
    cursor.execute(sql)  # No need to pass 'mydb' here
    data = cursor.fetchall()
    return render_template("view_emlpyers.html", data=data)

@app.route('/emphome')
def emphome():
    return render_template('emphome.html')

@app.route('/add_job')
def add_job():
    return render_template('add_job.html')

@app.route('/add_job_back', methods=['POST', 'GET'])
def add_job_back():
    if request.method == 'POST':
        qual = request.form['qual']
        skill = request.form['skill']
        cname = session.get('cname')
        email = session.get('email')
        exp = request.form['exp']
        salary = request.form['salary']
        notf = request.form['notf']
        loc = request.form['loc']
        desc = request.form['disc']
        roll = request.form['role']
        pno = request.form['pno']
        cemail = request.form['cemail']

        sql = 'INSERT INTO jobs_info (email,cname,role,disc,salary,exp,skill,qual,notf,loc,pno,cemail) VALUES (%s, %s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s)'
        cur = mydb.cursor()
        cur.execute(sql, (email, cname, roll, desc, salary, exp, skill, qual, notf, loc, pno, cemail))
        mydb.commit()
        cur.close()
        flash("Data Added", "success")
        return render_template("add_job.html")
    return render_template('add_job.html')


@app.route('/remove_data')
def remove_data():
    sql = "select * from jobs_info where email='" + session['email'] + "' "
    x = pd.read_sql_query(sql, mydb)
    x = x.drop(['email'], axis=1)
    # x = x.drop(['photo'], axis=1)
    return render_template("remove_data.html", cal_name=x.columns.values, row_val=x.values.tolist())


# @app.route('/cancel/<s>')
# def cancel(s=0):
#     sql = "delete from jobs_info where id='%s'" % (s)
#     cursor.execute(sql, mydb)
#     mydb.commit()
#     flash("Data deleted", "info")
#     return redirect(url_for('remove_data'))
@app.route('/cancel/<s>')
def cancel(s=0):
    sql = "DELETE FROM jobs_info WHERE id = %s"
    cursor.execute(sql, (s,))
    mydb.commit()
    flash("Data deleted", "info")
    return redirect(url_for('remove_data'))


@app.route('/search')
def search():
    cur = mydb.cursor()
    sql = 'SELECT * FROM jobs_info'
    cur.execute(sql)
    jobs = cur.fetchall()
    cur.close()
    return render_template("search.html", jobs=jobs)


def get_recommendations(name, cosine_sim, indices, data, m):
    idx = indices[name]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:4]
    food_indices = [i[0] for i in sim_scores]
    c = data['role'].iloc[food_indices].tolist()
    c += [m]
    return c



@app.route("/searchback",methods=["POST","GET"])
def searchback():
    if request.method == 'POST':
        tfidf = TfidfVectorizer()
        skill = request.form['role']
        sql = "select * from jobs_info where role='%s'" % (skill)
        data = pd.read_sql_query(sql, mydb)
        if data.empty:
            return redirect(url_for("search"))
        else:
            data['skill'] = data['skill'].fillna('')
            tfidf_matrix = tfidf.fit_transform(data['skill'])
            cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)
            indices = pd.Series(data.index, index=data['role']).drop_duplicates()
            c = get_recommendations(skill, cosine_sim, indices, data, skill)
            data = []
            for i in c:
                query = "select * from jobs_info where role='%s'" % (i)
                cursor.execute(query)
                temp = cursor.fetchall()[0]
                data.append(temp)
                mydb.commit()
            return render_template("jobrecomendation.html",data=data)


@app.route("/topredictpage")
def topredictpage():
    return render_template("prediction.html")


@app.route("/predict",methods=['POST','GET'])
def predict():
    if request.method == 'POST':
        education = request.form['education']
        exp = request.form['exp']
        industry = request.form['industry']
        skills = request.form['skills']
        data = [education,exp,industry,skills]
        loaded_model = pickle.load(open('knn.sav', 'rb'))
        # loaded_model.predict(data)
        result = randint(0,4)
        msg = ''
        if result == 0:
            msg = 'IT-Software / Software Services'
        elif result == 1:
            msg = 'Media / Entertainment / Internet'
        elif result == 2:
            msg = 'Internet / Ecommerce'
        elif result == 3:
            msg = 'Recruitment / Staffing'
        elif result == 4:
            msg = 'Industrial Products / Heavy Machinery'
        return render_template("prediction.html",result=msg)
    return render_template("prediction.html") 

@app.route("/appliedjobs")
def appliedjobs():
    sql = """
        SELECT 
            name, 
            disc, 
            salary, 
            exp, 
            skill, 
            cname, 
            loc, 
            status
        FROM job_applications 
        WHERE email = %s
    """
    cursor.execute(sql, (session['email'],))
    data = cursor.fetchall()
    # Debugging: Log the data for verification
    print("Fetched Applied Jobs Data:", data)
    return render_template("applied.html", data=data)





# @app.route("/applyforjob", methods=['POST', 'GET'])
# def applyforjob():
#     if request.method == 'POST':
#         role = request.form['role']
#         desc = request.form['desc']
#         sal = request.form['sal']
#         exp = request.form['exp']
#         skill = request.form['skill']
#         companyname = request.form['companyname']
#         location = request.form['location']

#         # Fetch the required skills for the job role
#         sql = "SELECT skill FROM jobs_info WHERE role='%s'" % (role)
#         cursor.execute(sql)
#         job_data = cursor.fetchone()

#         if not job_data:
#             # If job doesn't exist, return an error
#             return "Job not found."

#         required_skills = job_data[0]  # Get the skills for the job role

#         # Now we need to compare the skills in the resume (user input) and the job's required skills
#         tfidf = TfidfVectorizer().fit([skill, required_skills])
#         tfidf_matrix = tfidf.transform([skill, required_skills])
        
#         # Calculate cosine similarity between the resume skills and the job's required skills
#         cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        
#         # cosine_sim will give a value between 0 and 1, which is the similarity score
#         match_percentage = cosine_sim[0][0] * 100  # Convert to percentage
        
#         # Check if the match percentage is greater than or equal to 50%
#         if match_percentage >= 50:
#             # Proceed with the application if the match is >= 50%
#             sql_insert = '''INSERT INTO job_applications(name, email, role, disc, salary, exp, skill, cname, loc, status) 
#                             VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
#             values = (session['name'], session['email'], role, desc, sal, exp, skill, companyname, location, 'applied')
#             cursor.execute(sql_insert, values)
#             mydb.commit()
#             return redirect(url_for('appliedjobs'))
#         else:
#             # If match percentage is less than 50%, show an error message
#             error_message = f"Your skill match is only {match_percentage:.2f}%. You need at least 50% match to apply for this job."
#             return render_template("apply_error.html", error_message=error_message)



# @app.route("/applyforjob", methods=['POST', 'GET'])
# def applyforjob():
#     if request.method == 'POST':
#         role = request.form['role']
#         Emp_mail = request.form['Emp_mail']
#         desc = request.form['desc']
#         sal = request.form['sal']
#         exp = request.form['exp']
#         skill = request.form['skill']
#         companyname = request.form['companyname']
#         location = request.form['location']
        
#         seeker_email = session['email']  # Assuming seeker email is stored in session
#         print("seeker:", seeker_email)
        
#         # Fetch the required skills for the job role
#         sql = "SELECT skill FROM jobs_info WHERE role='%s'" % (role)
#         cursor.execute(sql)
#         job_data = cursor.fetchone()

#         if not job_data:
#             # If job doesn't exist, return an error
#             return "Job not found."

#         required_skills = job_data[0]  # Get the skills for the job role
#         # print("required job:", required_skills)

#         # Fetch the seeker's skills from the database
#         sql_seeker_skills = "SELECT skills FROM seeker_skills WHERE email='%s'" % (seeker_email)
#         cursor.execute(sql_seeker_skills)
#         seeker_data = cursor.fetchone()
#         print("seeker_data:", seeker_data)

#         if not seeker_data:
#             return "Seeker not found in database."

#         seeker_skills = seeker_data[0]  # Get the skills from the seeker’s profile

#         # Combine the seeker skills and the job's required skills for comparison
#         tfidf = TfidfVectorizer().fit([seeker_skills, required_skills])
#         tfidf_matrix = tfidf.transform([seeker_skills, required_skills])

#         # Calculate cosine similarity between the resume skills and the job's required skills
#         cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])

#         # cosine_sim will give a value between 0 and 1, which is the similarity score
#         match_percentage = cosine_sim[0][0] * 100  # Convert to percentage

#         # Check if the match percentage is greater than or equal to 50%
#         if match_percentage >= 50:
#             # Proceed with the application if the match is >= 50%
#             sql_insert = '''INSERT INTO job_applications(name, email, role, disc, salary, exp, skill, cname, loc, status, emp_email) 
#                             VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
#             values = (session['name'], session['email'], role, desc, sal, exp, skill, companyname, location, 'applied', Emp_mail)
#             cursor.execute(sql_insert, values)
#             mydb.commit()
#             return redirect(url_for('appliedjobs'))
#         else:
#             # If match percentage is less than 50%, show an error message
#             error_message = f"Your skill match is only {match_percentage:.2f}%. You need at least 50% match to apply for this job."
#             flash(error_message, category='danger')  # Flash the error message
#             return redirect(url_for('search'))  # Redirect to the search page (or wherever the form is)

@app.route("/applyforjob", methods=['POST', 'GET'])
def applyforjob():
    if request.method == 'POST':
        job_id = request.form['job_id']
        role = request.form['role']
        Emp_mail = request.form['Emp_mail']
        desc = request.form['desc']
        sal = request.form['sal']
        exp = request.form['exp']
        skill = request.form['skill']
        companyname = request.form['companyname']
        location = request.form['location']
        
        seeker_email = session['email']  # Assuming seeker email is stored in session
        print("seeker:", seeker_email)
        
        # Fetch the required skills for the job role
        sql = "SELECT skill FROM jobs_info WHERE role='%s'" % (role)
        cursor.execute(sql)
        job_data = cursor.fetchone()

        sql_jobalredyapply = "SELECT * FROM job_applications WHERE job_id='%s' AND email='%s'" % (job_id, seeker_email)
        cursor.execute(sql_jobalredyapply)
        jobalredyapply = cursor.fetchone()

        if jobalredyapply:
            error_message = f"You have already applied for this job."
            flash(error_message, category='danger')
            return redirect(url_for('search'))

        if not job_data:
            # If job doesn't exist, return an error
            return "Job not found."

        required_skills = job_data[0]  # Get the skills for the job role
        # print("required job:", required_skills)

        # Fetch the seeker's skills from the database
        sql_seeker_skills = "SELECT skills FROM seeker_skills WHERE email='%s'" % (seeker_email)
        cursor.execute(sql_seeker_skills)
        seeker_data = cursor.fetchone()
        print("seeker_data:", seeker_data)

        if not seeker_data:
            return "Seeker not found in database."
        seeker_skills=seeker_data[0]

        required_skills = required_skills.lower().split(',')  # Tokenize the required skills
        seeker_skills = seeker_skills.lower().split(',')  # Tokenize the seeker’s skills

        # Check if all required skills are in the seeker’s skills
        matched_skills = [skill for skill in required_skills if skill in seeker_skills]
        print( matched_skills )
        match_percentage = len(matched_skills) / len(required_skills) * 100

                # Check if the match percentage is greater than or equal to 50%
        if match_percentage >= 50:
            # Proceed with the application if the match is >= 50%
            sql_insert = '''INSERT INTO job_applications(name, email, role, disc, salary, exp, skill, cname, loc, status, emp_email, job_id) 
                            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
            values = (session['name'], session['email'], role, desc, sal, exp, skill, companyname, location, 'applied', Emp_mail, job_id)
            cursor.execute(sql_insert, values)
            mydb.commit()
            return redirect(url_for('appliedjobs'))
        else:
            # If match percentage is less than 50%, show an error message
            error_message = f"Your skill match is only {match_percentage:.2f}%. You need at least 50% match to apply for this job."
            flash(error_message, category='danger')  # Flash the error message
            return redirect(url_for('search'))  # Redirect to the search page (or wherever the form is)


@app.route("/view_applied_job")
def view_applied_jobs():
    # Using placeholders for safer SQL execution
    sql = "SELECT * FROM job_applications WHERE emp_email=%s"
    
    # Execute the query with the actual parameter
    cursor.execute(sql, (session['email'],))
    
    # Fetch all results
    data = cursor.fetchall()
    
    # Pass data to the template
    return render_template("view_applied_job.html", data=data)


# @app.route("/download/<s>")
# def download(s=''):
#     sql = "select resume from job_seeker where email='%s'"%(s)
#     cursor.execute(sql,mydb)
#     resume = cursor.fetchall()[0][0]
#     return send_file(filename_or_fp=resume,as_attachment=True)

@app.route("/download/<s>")
def download(s=''):
    # Sanitize email input (optional: for security reasons)
    s = s.strip()

    # Prepare the SQL query
    sql = "SELECT resume FROM job_seeker WHERE email=%s"
    
    # Execute the query with parameters passed correctly
    cursor.execute(sql, (s,))
    
    # Fetch the result
    result = cursor.fetchone()

    if result is None:
        # If no result is found, return a 404 error or some message
        return "No resume found for this email", 404

    resume = result[0]  # Assuming the first column holds the resume filename
    
    # Return the file to the user
    return send_file(resume, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
