import json, os, shutil, uuid
import numpy as np
from load_saved_model import load_model
import os
from pathlib import Path
model = load_model()

DOCTORS_PATH = os.path.join("static", "doctors")

def save_user(data):
    with open("users.json", "r") as json_file:
        list_of_dic = json.load(json_file)
    pre_dictionary_of_user_pass = list_of_dic[0]
    username = data["username"]
    password = data["pass"]
    confirm_password = data["cpass"]
    if username and password and confirm_password:
        if username not in pre_dictionary_of_user_pass:
            if password == confirm_password:
                pre_dictionary_of_user_pass.update({username:password})
                json_object = json.dumps([pre_dictionary_of_user_pass])

                with open("users.json", "w") as json_file:
                    json_file.write(json_object)

                return 0, "Account Created Successfully, Now You Can Login"
                
            else:
                return 1, "Your Confirm Pass Is Different, Type Carefully"
        else:
            return 2, "This Email exists, If Is Yours, Please Login"
            

def check_login(data):
    with open("users.json", "r") as json_file:
        list_of_dic = json.load(json_file)
    pre_dictionary_of_user_pass = list_of_dic[0]
    username = data["username"]
    password = data["pass"]

    if username and password:
        if username not in pre_dictionary_of_user_pass:
            return 1 ,"Username Doesn't exist, Please Sign Up"
        
        else:
            if pre_dictionary_of_user_pass[username] == password:
                return 0, "Successfully Loged In"
            else:
                return 2, "Password Isn't Correct, Try Again"

    
def get_unique_folder_id(id:int):
    id = int(id)
    np.random.seed(id)
    folder_id = np.random.randint(1, 100000)
    return folder_id
        
def get_patient(user, search_id=None):
    root_path = os.path.join(DOCTORS_PATH, user)

    if not os.path.exists(root_path):
        os.mkdir(root_path)

    if search_id:
        patients_path = [get_unique_folder_id(search_id)]
        if not patients_path[0]: patients_path=[] 
    else:
        patients_path = os.listdir(root_path)

#     items_with_creation_times = [(item, Path(root_path) / item) for item in patients_path]

# # Sort the list based on the creation time
#     sorted_items = sorted(items_with_creation_times, key=lambda x: os.stat(x[1]).st_ctime)
#     patients_path = [item[0] for item in sorted_items]
    # print(patients_path)
    patients = {}
    contents = {}
    for folder_name in patients_path:
        json_path = os.path.join(root_path, str(folder_name))
        
        if os.path.isdir(json_path) == False or folder_name == "equivilant.json" or folder_name == "fast-mri.png": continue
        
        with open(os.path.join(json_path, "patient.json"), "r") as json_file:
            pre_dictionary = json.load(json_file)[0]
            id = pre_dictionary["i"]
        
        patients.update({id: pre_dictionary})
    contents.update({"user":user, "patients" : patients})
    # print(contents)
    return contents
            
def save_dashboard(datas):
    user = datas["u"]
    id = datas["i"]
    mri_img = datas["m"]
    datas.pop("m")

    ## Check if alrady exist 
    # patients = get_patient(user)["patients"]
    # if id in patients:
    #     return False 
    ## 

    if not id and mri_img != "":
        mri_img.save(os.path.join(DOCTORS_PATH, user, "fast-mri.png" ))
        return True

    if "diagnose" not in datas:
        datas["diagnose"] = ""
    folder_name = get_unique_folder_id(id)
   
    patient_root_path = os.path.join(DOCTORS_PATH, user, str(folder_name))
    
    if not os.path.exists(patient_root_path):
        os.mkdir(patient_root_path)
    
    pateint_json_dir = os.path.join(patient_root_path, "patient.json")
    if os.path.exists(pateint_json_dir):
        with open(pateint_json_dir, "r") as json_file:
            pre_dictionary = json.load(json_file)[0]

        for key, val in datas.items():
            if val == "" :
                datas.update({key:pre_dictionary[key]})

    datas.update({"folder_id":folder_name})
    json_object = json.dumps([datas])
    with open(pateint_json_dir, "w") as json_file:
        json_file.write(json_object)

    pateint_mri_dir = os.path.join(patient_root_path, "mri.png")
    if mri_img.filename != "":
        mri_img.save(pateint_mri_dir)


    return True

        
def delete_patient(user, id):
    # id = int(id)
    folder_id = get_unique_folder_id(id)
    root_path = os.path.join(DOCTORS_PATH, user, str(folder_id))
    shutil.rmtree(root_path, ignore_errors=True)
    return True
    
def delete_file(user, id):
    folder_id = get_unique_folder_id(id)
    file_path = os.path.join(DOCTORS_PATH, user, str(folder_id),"mri.png")
    os.remove(file_path)
    return True

def mri_diagnose(user, id=0):
    id = int(id)
    folder_path = os.path.join(DOCTORS_PATH, user)
    image_path = os.path.join(folder_path, "fast-mri.png")

    if id :
        id = get_unique_folder_id(id)
        folder_path = os.path.join(folder_path, str(id))
        image_path = os.path.join(folder_path ,"mri.png")   

    
    if os.path.isfile(image_path):
        result = model.predict(image_path)
        
        if id:
            with open(file=os.path.join(folder_path, "patient.json"), mode="r") as json_file:
                pre_dictionary = json.load(json_file)[0]
            pre_dictionary["diagnose"] = result

            json_object = json.dumps([pre_dictionary])
            with open(file=os.path.join(folder_path, "patient.json"), mode="w") as json_file:
                json_file.write(json_object)
            
    else:
        result = "Erorr"
    


    return result
    


    
        


    