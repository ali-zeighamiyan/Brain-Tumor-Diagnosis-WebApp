from sqlalchemy import Column, ForeignKey, Integer, String, Date, LargeBinary
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import bcrypt, io
from PIL import Image
from datetime import datetime
from sqlalchemy import select
import smtplib

EMAIL_HOST = "smtp.gmail.com"
EMAIL_HOST_USER = "azb1378@gmail.com"
EMAIL_HOST_PASSWORD = "dkekzjnsjyzuabka"
EMAIL_PORT_SSL = 465

from load_saved_model import load_model
model = load_model()


class Base(DeclarativeBase):
    pass


class Doctor(Base):
    
    __tablename__ = 'doctors'
    email = Column(String(100), primary_key=True, nullable=False)
    password_hash = Column(Integer, nullable=False)
    name = Column(String(100), nullable=True)
    bio = Column(String, nullable=True)
    patient_table = relationship("Patient", back_populates="doctor_table")

class Patient(Base):
    __tablename__ = 'patients'
    id = Column(String, primary_key=True)
    doctor_email = Column(String, ForeignKey('doctors.email'), primary_key=True)
    firstname = Column(String(30), nullable=False)
    lastname = Column(String(50), nullable=False)
    diagnose = Column(String(100), nullable=False)
    image_bytes = Column(LargeBinary, nullable=False)
    service_date = Column(Date, nullable=False)
    note = Column(String(100), nullable=False)
    doctor_table = relationship("Doctor", back_populates="patient_table")


class SendMail:
    def __init__(self):
        server = smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT_SSL)
        self.server = server

    def ckeck_user_exist(self, user_email):
        
        self.user_email = user_email
        self.doctor = session.query(Doctor).filter_by(email=self.user_email).first()
        if self.doctor: return 1 
        else : return 0
    def send_email(self, user_email, token):
        self.token = token
        self.user_email = user_email
        with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT_SSL) as server:
            server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            server.sendmail(EMAIL_HOST_USER, self.user_email, self.token)
        return 1
            
        

# Create the database engine
engine = create_engine('sqlite:///datafile.db')

# Create the tables in the database
# Base.metadata.create_all(engine)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

# Create doctors
def add_user(data):
    username = data["username"]
    doctor = list(session.scalars(select(Doctor).where(Doctor.email.in_([username]))))
    if not len(doctor):
        password = data["pass"]
        confirm_password = data["cpass"]
        if password == confirm_password:
            password = password.encode("utf-8")
            password_hash = bcrypt.hashpw(password, bcrypt.gensalt())
            doctor = Doctor(email=username, password_hash=password_hash)
            session.add(doctor)
            session.commit()
            return 0, "Account Created Successfully, Now You Can Login"
        else:
            return 1, "Your Confirm Pass Is Different, Type Carefully"
    else:
        return 2, "This Email exists, If Is Yours, Please Login"

def check_login(data):
    username = data["username"]
    input_password = data["pass"].encode("utf-8")

    doctor_row = session.query(Doctor).filter_by(email=username).first()

    if (doctor_row):

        saved_password_hash = doctor_row.password_hash

        if bcrypt.checkpw(input_password, saved_password_hash):
            return 0, "Successfully Loged In"
        else:
            return 2, "Password Isn't Correct, Try Again"
    
    else:
        return 1 ,"Username Doesn't exist, Please Sign Up"

def convert_bytes_image(image_bytes):
    image_bytes = io.BytesIO(image_bytes)
    return Image.open(image_bytes)


def save_patient(datas):
    username = datas["u"]
    id_number = datas["i"]
    mri_img = datas["m"].read()
    firstname = datas["f"]
    lastname = datas["l"]
    note = datas["n"].replace('\r', '\\r').replace('\n', '\\n')
    if datas["d"] == "":
        date = datetime.now()
    else:
        date = datetime.strptime(datas["d"], "%Y-%m-%d")


    doctor_patient = session.scalars(select(Patient).filter_by(id=id_number).filter_by(doctor_email=username)).all()

    ##### Create patient if it not exists
    if not doctor_patient:
        if mri_img != b"":
            diagnose = model.predict(convert_bytes_image(mri_img))
        else :
            diagnose = ""

        doctor = session.scalars(select(Doctor).where(Doctor.email.in_([username]))).one()
        patient = Patient(id=int(id_number), firstname=firstname, lastname=lastname, diagnose=diagnose, image_bytes=mri_img, service_date=date, note=note, doctor_table=doctor)
        session.add_all([patient])

    ##### Edit patient if it exists
    else:
        if mri_img != b"":
            diagnose = model.predict(convert_bytes_image(mri_img))
            doctor_patient[0].image_bytes = mri_img
            doctor_patient[0].diagnose = diagnose

        doctor_patient[0].lastname = lastname
        doctor_patient[0].firstname = firstname
        doctor_patient[0].note = note.replace('\r', '\\r').replace('\n', '\\n')
        doctor_patient[0].service_date = date
        

    
    session.commit()


def get_patient(username, search_id=None):

    if search_id:
        patients = session.scalars(select(Patient).filter_by(id=search_id).filter_by(doctor_email=username)).all()

    else:
        patients = session.scalars(select(Patient).filter_by(doctor_email=username)).all()

    patients_dictionary = {}
    contents = {}
    for patient in patients:
        patients_dictionary.update({patient.id : {"u": username, "f": patient.firstname, "l": patient.lastname, "i": patient.id, "d": patient.service_date, "n": patient.note, "diagnose": patient.diagnose}})


    contents.update({"user":username, "patients" : patients_dictionary})
    return contents


def delete_patient(username, id, just_delete_image=None):
    row_to_delete = session.query(Patient).filter_by(id=id).filter_by(doctor_email=username).first()
    if row_to_delete:
        if just_delete_image:
            row_to_delete.image_bytes = b""
            row_to_delete.diagnose = ""
        else:
            session.delete(row_to_delete)
        session.commit()
        return True


def fast_diagnose(datas):
    mri_img = datas["m"].read()
    if mri_img != b"":
        diagnose = model.predict(convert_bytes_image(mri_img))
    else:
        diagnose = ""
    
    return diagnose


def get_patient_image(username, id):
    image_row = session.query(Patient).filter_by(id=id).filter_by(doctor_email=username).first()
    if image_row:
        image_bytes = image_row.image_bytes
        return io.BytesIO(image_bytes)

def update_password(new_password, user_email):
    doctor = session.query(Doctor).filter_by(email=user_email).first()
    new_password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
    doctor.password_hash = new_password_hash
    return 1


def modify_user_inf(datas):
    username = datas["u"]
    name = datas["n"]
    bio = datas["b"].replace('\r', '\\r').replace('\n', '\\n')
    input_password = datas["p"]
    new_password = datas["np"]
    new_email = datas["ne"]

    user_or_pass_changed = False

    doctor = session.query(Doctor).filter_by(email=username).first()
    

    if input_password and new_password:
        saved_password_hash = doctor.password_hash
        input_password = input_password.encode("utf-8")
        if bcrypt.checkpw(input_password, saved_password_hash):
            mes_type = update_password(new_password, username)
            user_or_pass_changed = True
        else:
            return -1

    if new_email and new_email != username:
        doctor_new_email = session.query(Doctor).filter_by(email=new_email).first()
        if not doctor_new_email:
            doctor.email = new_email
            doctor_patient = session.query(Patient).filter(Patient.doctor_email==username).update({"doctor_email":new_email})
            mes_type = 2
            user_or_pass_changed = True
        else:
            return -2
    
    if not user_or_pass_changed:
        mes_type = 0
    
    doctor.name = name
    doctor.bio = bio
    
    session.commit()
    return mes_type

def get_user_inf(username):
    doctor = session.query(Doctor).filter_by(email=username).first()
    name = doctor.name 

    bio = doctor.bio
    bio = bio
    contents={"u":username, "b":bio , "n":name}

    return contents














