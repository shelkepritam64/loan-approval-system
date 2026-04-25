from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import numpy as np
import pandas as pd
import mysql.connector

app = Flask(__name__)
CORS(app)

# Load all required files
model = pickle.load(open("model.pkl", "rb"))
scaler = pickle.load(open("scaler.pkl", "rb"))
feature_columns = pickle.load(open("columns.pkl", "rb"))

# ========== MySQL Connection ==========
# ⚠️ CHANGE "YOUR_PASSWORD" to your actual MySQL root password
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Pritam@6458"
    )
    cursor = db.cursor()
    
    # Create database if it doesn't exist
    cursor.execute("CREATE DATABASE IF NOT EXISTS loan_system")
    db.database = "loan_system"
    
    # Create table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loan_applications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            credit_score FLOAT,
            income_annum FLOAT,
            loan_amount FLOAT,
            loan_term FLOAT,
            employment_status VARCHAR(50),
            name VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(20),
            gender VARCHAR(20),
            prediction_result VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.commit()
except Exception as e:
    print(f"Database connection error: {e}")

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()

        # Get input values safely
        credit_score = float(data.get('credit_score', 0))
        income = float(data.get('income_annum', 0))
        loan_amount = float(data.get('loan_amount', 0))
        loan_term = float(data.get('loan_term', 0))

        input_dict = {
            'credit_score': credit_score,
            'income_annum': income,
            'loan_amount': loan_amount,
            'loan_term': loan_term
        }

        # Convert to DataFrame
        input_df = pd.DataFrame([input_dict])

        # Match training columns (VERY IMPORTANT)
        input_df = input_df.reindex(columns=feature_columns, fill_value=0)

        # Scale input
        input_scaled = scaler.transform(input_df)

        # Predict
        prediction = model.predict(input_scaled)[0]

        # Final result
        result = "Approved" if prediction == 1 else "Rejected"

        # ========== Save to MySQL Database ==========
        # Check if full application (has name/email)
        is_full = data.get('name') and data.get('email')

        if is_full:
            cursor.execute("""
                INSERT INTO loan_applications
                (credit_score, income_annum, loan_amount, loan_term,
                 employment_status, name, email, phone, gender, prediction_result)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                credit_score,
                income,
                loan_amount,
                loan_term,
                data.get('employment_status'),
                data.get('name'),
                data.get('email'),
                data.get('phone'),
                data.get('gender'),
                result
            ))
            db.commit()

        return jsonify({
            "status": result
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        })


if __name__ == '__main__':
    app.run(debug=True)