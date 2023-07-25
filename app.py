from flask_cors import CORS
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from datetime import timedelta
from functions import save_user, check_login, save_dashboard, get_patient, delete_patient, mri_diagnose, delete_file
import json
app = Flask(__name__)
CORS(app)
app.secret_key = "Hellow"
app.permanent_session_lifetime = timedelta(days=1)


@app.route("/")
def home():
    
    session.permanent = True
    if 'username' in session:
        return render_template('index.html', message = "login")

    return render_template('index.html')
    

@app.route('/login', methods=["POST", "GET"])
def login():
        if request.method == "GET":
            if "message" in session:
                message = session['message']
                session.pop("message")  # counterpart for url_for()
                # messages = session['message']       # counterpart for session
                return render_template("login.html", messageg=message)
            else:
                return render_template("login.html")
        
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["pass"]
            data = {"username":username, "pass":password}
            mess_type, message = check_login(data)

            if mess_type == 1 or mess_type == 2:
                return render_template('login.html', messager=message)
            elif mess_type == 0:
                session["username"] = username
                session['message'] = message
                # session.pop("message")
                return redirect(url_for('dashboard'))



@app.route('/signup', methods=["POST", "GET"])
def signup():
    if request.method == "POST":
        # data = request.get_json(force=True)
        username = request.form["username"]
        password = request.form["pass"]
        confirm_password = request.form["cpass"]

        data = {"username":username, "pass":password, "cpass":confirm_password}
        
        mess_type, message = save_user(data)
        # return flask.Response(message, status=201)
        if mess_type == 1 or mess_type == 2:
            return render_template('signup.html', message=message)
        elif mess_type == 0:
            session['message'] = message
            return redirect(url_for('login'))


    if request.method == "GET" :
        return render_template('signup.html')
        
@app.route('/dashboard', methods=["POST", "GET"])
def dashboard():
    
    session.permanent = True
    if 'username' in session:
        username = session["username"]

        if request.method == "GET" :
            if "search_id" in request.args:
                search_id = request.args["search_id"]
                datas = get_patient(username, search_id=search_id)
            else:
                datas = get_patient(username)
                    # messages = session['message']       # counterpart for session
            if "message" in session:
                message = session["message"]
                session.pop('message', None)
                return render_template("dashboard.html", message=message, contents=datas)
            else:
                return render_template("dashboard.html", contents=datas)

            
        if request.method == "POST" :
                # if len(request.form):
                firstname = request.form["firstname"]
                lastname = request.form["lastname"]
                id_number = request.form["id-num"]
                date = request.form["date"]
                mri_image = request.files["mri-img"]
                note = request.form["note"]
                datas = {"u":username, "f":firstname, "l":lastname, "i":id_number, "d":date, "m":mri_image, "n":note}
                
                # else:
                #     mri_image = request.files["mri-img"]
                #     datas = {"u":username, "m":mri_image, "i":0}

                save_res = save_dashboard(datas)


                datas = get_patient(username)
                return render_template("dashboard.html", contents=datas)


    else:
        return redirect(url_for("login"))

@app.route('/edit', methods=["GET"])
def edit():
   if request.method == "GET":     
        return render_template("edit.html")
   

@app.route('/mri_images', methods=["POST", "GET"])
def mri_images():
   if request.method == "GET":
        return render_template("modal_image.html")



@app.route('/logout', methods=["POST", "GET"])
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))
    

@app.route('/delete', methods=["POST", "GET"])
def delete():
    if request.method == "GET" :
        user = session["username"]
        id = request.args.getlist('id')
        image = request.args.getlist("image")
        if id:
            if image:
                result = delete_file(user, id[0]) 

            else:
                result = delete_patient(user, id[0])
            
            return jsonify(result=result)

        else:
            return render_template('delete.html')
    
@app.route('/diagnose', methods=["POST", "GET"])
def diagnose():
    if "username" in session: 
        user = session["username"]
        if request.method == "GET" : 
            id = request.args.getlist('id[]')[0]
            result = mri_diagnose(user, id)
        
        if request.method == "POST" :
            mri_image = request.files["mri-img"]
            datas = {"u":user, "m":mri_image, "i":0}
            save_result = save_dashboard(datas)
            result = mri_diagnose(user)
        

        return jsonify(result = result)
    else:
        return redirect(url_for("login"))



if __name__ == "__main__":
    app.run("0.0.0.0", 6969, debug=False)

