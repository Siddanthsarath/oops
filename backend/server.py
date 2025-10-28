import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mail import Mail, Message
from dotenv import load_dotenv
from database import create_all_tables, session, User
import bcrypt
import random

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

app.config.update(
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_PORT=int(os.getenv("MAIL_PORT")),
    MAIL_USE_TLS=os.getenv("MAIL_USE_TLS") == "True",
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
)

mail = Mail(app)
create_all_tables()

def generate_otp():
    return str(random.randint(100000, 999999))

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    if session.query(User).filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400

    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    new_user = User(email=email, password=hashed_pw)
    session.add(new_user)
    session.commit()

    return jsonify({"message": "Registration successful!"})


@app.route("/login_request", methods=["POST"])
def login_request():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    user = session.query(User).filter_by(email=email).first()
    if not user or not bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
        return jsonify({"error": "Invalid credentials"}), 400

    otp = generate_otp()
    user.otp = otp
    session.commit()

    msg = Message("Login OTP", sender=os.getenv("MAIL_USERNAME"), recipients=[email])
    msg.body = f"Your login OTP is {otp}"
    mail.send(msg)

    return jsonify({"message": "Login OTP sent to email"})


@app.route("/login_verify", methods=["POST"])
def login_verify():
    data = request.json
    email = data.get("email")
    otp = data.get("otp")

    user = session.query(User).filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.otp == otp:
        user.otp = None
        session.commit()
        return jsonify({"message": "Login successful!"})
    else:
        return jsonify({"error": "Invalid OTP"}), 400


if __name__ == "__main__":
    app.run(debug=True)
