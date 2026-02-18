from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
from fastapi import FastAPI, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import sqlite3
from jose import JWTError, jwt
from datetime import datetime, timedelta

app = FastAPI()

SECRET_KEY = "secretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# ------------------ DATABASE ------------------

def create_tables():
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # JOBS TABLE (ONLY THIS ONE)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        company TEXT,
        location TEXT,
        salary TEXT
    )
    """)

    conn.commit()
    conn.close()


# ------------------ AUTH ------------------

def authenticate_user(username: str, password: str):
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username,password))
    existing_user = cursor.fetchone()
    user = cursor.fetchone()
    conn.close()
    return user


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ------------------ REGISTER ------------------

@app.post("/register")
def register(username: str = Form(...), password: str = Form(...)):
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()

    try:
        hashed_password = pwd_context.hash(password)

        cursor.execute(
          "INSERT INTO users (username, password) VALUES (?, ?)",
    (username, hashed_password)
)
    except:
        return {"error": "User already exists"}

    conn.close()
    return {"message": "User registered successfully"}


# ------------------ LOGIN ------------------

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": form_data.username})

    return {"access_token": access_token, "token_type": "bearer"}


# ------------------ PROTECTED ROUTE ------------------

@app.get("/protected")
def protected_route(token: str = Depends(oauth2_scheme)):
    return {"message": "You are authorized!"}
from pydantic import BaseModel
class Job(BaseModel):
    title: str
    company: str
    location: str
    salary: str

jobs = []
applications = []

@app.post("/create-job")
def create_job(job: Job):
    jobs.append(job)
    return {"message": "Job created successfully"}

@app.get("/jobs")
def get_jobs():
    return jobs

class Application(BaseModel):
    username: str
    job_title: str

@app.post("/apply")
def apply_job(application: Application):
    applications.append(application)
    return {"message": "Applied successfully"}

@app.get("/applications")
def get_applications():
    return applications
    