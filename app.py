from flask_cors import CORS
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_file, make_response
from datetime import datetime, timedelta
from app_functions import add_user, check_login, save_patient, delete_patient, fast_diagnose,\
                 delete_patient, get_patient, get_patient_image, get_user_inf, modify_user_inf, update_password, SendMail

import secrets


app = Flask(__name__)
CORS(app)
app.secret_key = "Hellow"
app.permanent_session_lifetime = timedelta(days=1)

RESET_TOKEN = {}
mail = SendMail()

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
        
        mess_type, message = add_user(data)
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

                save_res = save_patient(datas)


                datas = get_patient(username)
                return render_template("dashboard.html", contents=datas)


    else:
        return redirect(url_for("login"))

@app.route('/edit', methods=["GET"])
def edit():
   if request.method == "GET":     
        return render_template("edit.html")
   

@app.route('/get_image/<image_id>', methods=["POST", "GET"])
def get_image(image_id):
   if request.method == "GET":
        image_io = get_patient_image(session["username"], image_id)
        response = make_response(send_file(image_io, mimetype='image/jpeg'))
        return response

@app.route('/modal_image', methods=["GET"])
def modal_image():
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
                result = delete_patient(user, id[0], just_delete_image=True) 

            else:
                result = delete_patient(user, id[0])
            
            return jsonify(result=result)

        else:
            return render_template('delete.html')
    
@app.route('/diagnose', methods=["POST", "GET"])
def diagnose():
    if request.method == "POST" :
        mri_image = request.files["mri-img"]
        datas = {"m":mri_image}
        result = fast_diagnose(datas)
    

    return jsonify(result = result)


@app.route('/account', methods=["POST", "GET"])
def account():
    username = session["username"]

    if request.method == "GET":
        contents = get_user_inf(username)
        if "mess_type" in session:
            message = session["mess_type"]
            session.pop("mess_type")
            contents.update({"message":str(message)})
            return render_template("account.html", contents=contents)
        else:
            return render_template("account.html", contents=contents)


    if request.method == "POST":
        name = request.form["name"]
        new_email = request.form["email"]
        bio = request.form["bio"]
        password = request.form["password"]
        new_password = request.form["newpassword"]
        confirm_password = request.form["confirmpassword"]
        datas = {"u":username, "n":name, "b":bio, "p":password, "np":new_password, "cp":confirm_password, "ne":new_email }
        mes_type = modify_user_inf(datas)
        if mes_type == 2:
            session["username"] = new_email
        
        session["mess_type"] = mes_type
        
        return redirect(url_for("account"))

    
@app.route('/forgotpass', methods=["POST", "GET"])
def forgotpass():
    if request.method == "GET":
        return render_template("forgot_pass.html")
    
    if request.method == "POST":
        user_input_email = request.form["email"]

        #  Preventing Numerous Requests
        if user_input_email in RESET_TOKEN:
            token_expire_date = RESET_TOKEN[user_input_email][1]
            
            ## Check if Token Expired Then Delete It
            if token_expire_date - datetime.now() < timedelta(minutes=4) :
                RESET_TOKEN.pop(user_input_email)
    
            ## Send Message That Token Already Sended
            else:
                return jsonify(result = 2)
        
            
        if user_input_email:
                user_exist = mail.ckeck_user_exist(user_input_email)
                return jsonify(result = user_exist)


@app.route('/sendmail', methods=["POST", "GET"])
def sendmail():
    if request.method == "POST":
        user_input_email = request.form["email"]
        reset_token = secrets.token_hex(4)
        expire_date = datetime.now() + timedelta(minutes=5)
        send_email_res = mail.send_email(user_input_email, reset_token)
        RESET_TOKEN.update({user_input_email:[reset_token, expire_date]})
    
        return jsonify(result = send_email_res)

        
@app.route('/resetpass', methods=["POST"])
def resetpass():
    user_input_token = request.form["token"]
    new_password = request.form["newpassword"]
    user_input_email = list(RESET_TOKEN.keys())[0]

    if user_input_token and user_input_email in RESET_TOKEN :

        reset_token = RESET_TOKEN[user_input_email][0]
        token_expire_date = RESET_TOKEN[user_input_email][1]

        if token_expire_date > datetime.now() :
            if reset_token == user_input_token :
                update_password(new_password, user_input_email)
                RESET_TOKEN.pop(user_input_email)
                
                return jsonify(result = 1)
            ### Token Has Expired
            else:
                return jsonify(result = 0)
        else:
            RESET_TOKEN.pop(user_input_email)
            return jsonify(result = -1)




if __name__ == "__main__":
    app.run("0.0.0.0", 8000, debug=False)

