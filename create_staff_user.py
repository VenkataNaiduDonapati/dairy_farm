from werkzeug.security import generate_password_hash
import mysql.connector

# Replace with your actual MySQL credentials
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="dairy_farm"
)

cursor = db.cursor()

# Set your desired username and password
username = "Naidu"
password = "Naidu123@"

# Hash the password
hashed_password = generate_password_hash(password)

# Insert into staff table
try:
    cursor.execute("INSERT INTO staff (username, password_hash) VALUES (%s, %s)", (username, hashed_password))
    db.commit()
    print("✅ Staff user created successfully.")
except mysql.connector.Error as err:
    print("❌ Error:", err)

cursor.close()
db.close()