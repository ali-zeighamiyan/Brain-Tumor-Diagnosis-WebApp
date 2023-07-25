from sqlalchemy import Column, ForeignKey, Integer, String, Date, Table, LargeBinary
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import bcrypt, io
from PIL import Image
from datetime import datetime
from sqlalchemy import select, delete


from load_saved_model import load_model
model = load_model()


class Base(DeclarativeBase):
    pass


class Doctor(Base):
    
    __tablename__ = 'doctors'
    email = Column(String(100), primary_key=True, nullable=False)
    password_hash = Column(Integer, nullable=False)
    name = Column(String(100), nullable=True)
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

# class DoctorPatient(Base):
#     __tablename__ = 'doctor_patient'
#     doctor_email = Column(Integer, ForeignKey('doctors.email'), primary_key=True)
#     patient_id = Column(Integer, ForeignKey('patients.id'), primary_key=True)


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

    doctor_row = session.scalars(select(Doctor).where(Doctor.email.in_([username]))).one()

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
    mri_img = datas["m"]
    firstname = datas["f"]
    lastname = datas["l"]
    note = datas["n"]
    date = datetime.strptime(datas["d"], "%Y/%m/%d")

    if mri_img != "":
        diagnose = model.predict2(convert_bytes_image(mri_img))
    else:
        diagnose = ""
    
    doctor_patient = session.scalars(select(Patient).filter_by(id=id_number).filter_by(doctor_email=username)).all()

    if not doctor_patient:
        doctor = session.scalars(select(Doctor).where(Doctor.email.in_([username]))).one()
        patient = Patient(id=int(id_number), firstname=firstname, lastname=lastname, diagnose=diagnose, image_bytes=mri_img, service_date=date, note=note, doctor_table=doctor)
        session.add_all([patient])

    else:
        doctor_patient[0].lastname = lastname
        doctor_patient[0].firstname = firstname
        doctor_patient[0].image_bytes = mri_img
        doctor_patient[0].note = note
        doctor_patient[0].service_date = date
        doctor_patient[0].diagnose = diagnose

    
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


def delete_patient(username, id):
    row_to_delete = session.query(Patient).filter_by(id=id).filter_by(doctor_email=username).first()
    if row_to_delete:
        session.delete(row_to_delete)
        session.commit()
        return True


def fast_diagnose(datas):
    mri_img = datas["m"]
    if mri_img != "":
        diagnose = model.predict2(convert_bytes_image(mri_img))
    else:
        diagnose = ""
    
    return diagnose

















# print(add_user({"username":"azb@3516", "pass":"1234", "cpass":"1234"}))
# print(check_login({"username":"azb@3516", "pass":"1234"}))

# with open("Te-gl_0013.png", "rb") as imagefile:
#     image_bytes = imagefile.read()

# datas = {"u":"azb@3516", "f":"ali", "l":"zeigh", "i":"234", "d":"2022/03/05", "m":image_bytes, "n":"hey you"}

# save_patient(datas)

# print(get_patient("ali@3516", search_id="23"))
delete_patient("ali@3516", "356")
