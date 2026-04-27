"""
Banking Loan Risk Assessment System — Flask Backend
Full-stack application with ML risk scoring, admin dashboard, and audit logging.
"""
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, Response
from flask_cors import CORS
import pickle
import numpy as np
import pandas as pd
import mysql.connector
from functools import wraps
import os, json, csv, io, math
from datetime import datetime

# ========== App Config ==========
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '..', 'Frontend', 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), '..', 'Frontend', 'static')
)
app.secret_key = 'banking_risk_system_secret_2026'
CORS(app)

# ========== Load ML Models ==========
# New risk model (primary)
try:
    risk_model = pickle.load(open("risk_model.pkl", "rb"))
    risk_scaler = pickle.load(open("risk_scaler.pkl", "rb"))
    risk_columns = pickle.load(open("risk_columns.pkl", "rb"))
    USE_RISK_MODEL = True
    print("[OK] Risk model loaded successfully")
except Exception as e:
    USE_RISK_MODEL = False
    print(f"[WARN] Risk model not found: {e}")

# Old model (fallback)
try:
    old_model = pickle.load(open("model.pkl", "rb"))
    old_scaler = pickle.load(open("scaler.pkl", "rb"))
    old_columns = pickle.load(open("columns.pkl", "rb"))
    print("[OK] Legacy model loaded")
except:
    old_model = None

# ========== MySQL Connection ==========
db = None
cursor = None

def get_db():
    """Get or create MySQL connection."""
    global db, cursor
    try:
        if db and db.is_connected():
            return db
    except:
        pass

    try:
        db = mysql.connector.connect(
            host="localhost", user="root", password="Pritam@6458"
        )
        cursor = db.cursor(dictionary=True)
        cursor.execute("CREATE DATABASE IF NOT EXISTS loan_system")
        db.database = "loan_system"

        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loan_applications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                credit_score FLOAT, income_annum FLOAT, loan_amount FLOAT, loan_term FLOAT,
                existing_loans INT DEFAULT 0, existing_emis FLOAT DEFAULT 0,
                dti_ratio FLOAT DEFAULT 0, collateral_value FLOAT DEFAULT 0,
                ltv_ratio FLOAT DEFAULT 0, bank_balance FLOAT DEFAULT 0,
                previous_defaults INT DEFAULT 0, age INT DEFAULT 0,
                employment_status VARCHAR(50), years_of_employment INT DEFAULT 0,
                name VARCHAR(255), email VARCHAR(255), phone VARCHAR(20), gender VARCHAR(20),
                prediction_result VARCHAR(20), risk_score FLOAT DEFAULT 0,
                risk_level VARCHAR(20), emi_amount FLOAT DEFAULT 0,
                fraud_flags TEXT, feature_importance TEXT,
                application_type VARCHAR(20) DEFAULT 'quick',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_risk_score (risk_score), INDEX idx_prediction (prediction_result),
                INDEX idx_employment (employment_status), INDEX idx_created (created_at)
            )
        """)

        # Add missing columns to existing table
        new_cols = [
            ("existing_loans", "INT DEFAULT 0"), ("existing_emis", "FLOAT DEFAULT 0"),
            ("dti_ratio", "FLOAT DEFAULT 0"), ("collateral_value", "FLOAT DEFAULT 0"),
            ("ltv_ratio", "FLOAT DEFAULT 0"), ("bank_balance", "FLOAT DEFAULT 0"),
            ("previous_defaults", "INT DEFAULT 0"), ("age", "INT DEFAULT 0"),
            ("years_of_employment", "INT DEFAULT 0"), ("risk_score", "FLOAT DEFAULT 0"),
            ("risk_level", "VARCHAR(20)"), ("emi_amount", "FLOAT DEFAULT 0"),
            ("fraud_flags", "TEXT"), ("feature_importance", "TEXT"),
            ("application_type", "VARCHAR(20) DEFAULT 'quick'")
        ]
        for col, ctype in new_cols:
            try:
                cursor.execute(f"ALTER TABLE loan_applications ADD COLUMN {col} {ctype}")
            except:
                pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                admin_username VARCHAR(100), action VARCHAR(100),
                ip_address VARCHAR(50), details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()
        return db
    except Exception as e:
        print(f"DB Error: {e}")
        return None

get_db()

# ========== Admin Credentials ==========
ADMIN_USERNAME = "admin@123"
ADMIN_PASSWORD = "ad@123"

# ========== Helpers ==========
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def log_admin_action(action, details=""):
    try:
        conn = get_db()
        if conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO admin_logs (admin_username, action, ip_address, details) VALUES (%s,%s,%s,%s)",
                (ADMIN_USERNAME, action, request.remote_addr, details)
            )
            conn.commit()
            cur.close()
    except:
        pass

def get_interest_rate(risk_score):
    if risk_score <= 30:
        return 8
    elif risk_score <= 60:
        return 10
    else:
        return 14

def calculate_emi(P, annual_rate, N):
    if N <= 0 or P <= 0:
        return 0
    R = annual_rate / (12 * 100)
    if R == 0:
        return P / N
    emi = (P * R * (1 + R)**N) / ((1 + R)**N - 1)
    return round(emi, 2)

def detect_fraud(data):
    """Flag unrealistic values."""
    flags = []
    if data.get('credit_score', 0) > 900 or data.get('credit_score', 0) < 300:
        flags.append("Invalid credit score range")
    if data.get('income_annum', 0) > 50000000:
        flags.append("Unusually high income reported")
    if data.get('age', 0) < 18:
        flags.append("Applicant under 18")
    if data.get('age', 0) > 100:
        flags.append("Unrealistic age reported")
    if data.get('loan_amount', 0) > data.get('income_annum', 1) * 20:
        flags.append("Loan amount exceeds 20x annual income")
    if data.get('bank_balance', 0) < 0:
        flags.append("Negative bank balance")
    if data.get('previous_defaults', 0) > 5:
        flags.append("Excessive reported defaults")
    return flags

def get_risk_explanation(data, risk_score, feature_imp):
    """Generate top 3 human-readable reasons for the decision."""
    reasons = []
    cs = data.get('credit_score', 650)
    dti = data.get('dti_ratio', 0)
    ltv = data.get('ltv_ratio', 0)
    defaults = data.get('previous_defaults', 0)
    emp = data.get('employment_status', '')

    if cs < 550:
        reasons.append({"factor": "Low Credit Score", "detail": f"Score of {cs} is below the preferred threshold of 650", "impact": "high"})
    elif cs >= 750:
        reasons.append({"factor": "Excellent Credit Score", "detail": f"Score of {cs} indicates strong creditworthiness", "impact": "positive"})

    if dti > 0.5:
        reasons.append({"factor": "High Debt-to-Income Ratio", "detail": f"DTI of {dti:.1%} exceeds the safe limit of 40%", "impact": "high"})
    elif dti < 0.2:
        reasons.append({"factor": "Low Debt-to-Income Ratio", "detail": f"DTI of {dti:.1%} shows strong repayment capacity", "impact": "positive"})

    if ltv > 0.9:
        reasons.append({"factor": "High Loan-to-Value Ratio", "detail": f"LTV of {ltv:.1%} means minimal collateral coverage", "impact": "high"})

    if defaults > 0:
        reasons.append({"factor": "Previous Defaults", "detail": f"{defaults} previous default(s) on record", "impact": "high"})

    if emp == 'Unemployed':
        reasons.append({"factor": "Employment Status", "detail": "Currently unemployed increases repayment risk", "impact": "high"})
    elif emp == 'Employed':
        reasons.append({"factor": "Stable Employment", "detail": "Currently employed with regular income", "impact": "positive"})

    if len(reasons) < 3 and risk_score <= 30:
        reasons.append({"factor": "Overall Strong Profile", "detail": "Financial indicators suggest low risk", "impact": "positive"})
    elif len(reasons) < 3 and risk_score > 60:
        reasons.append({"factor": "Multiple Risk Factors", "detail": "Combined financial indicators suggest elevated risk", "impact": "high"})

    # Sort: high impact first, then positive
    reasons.sort(key=lambda x: 0 if x['impact'] == 'high' else 1)
    return reasons[:3]

# ========== Routes ==========

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    """Main prediction endpoint for the web form."""
    try:
        data = request.get_json()
        credit_score = float(data.get('credit_score', 650))
        income = float(data.get('income_annum', 0))
        loan_amount = float(data.get('loan_amount', 0))
        loan_term = float(data.get('loan_term', 12))
        existing_loans = int(data.get('existing_loans', 0))
        existing_emis = float(data.get('existing_emis', 0))
        collateral_value = float(data.get('collateral_value', 0)) or loan_amount * 1.2
        age = int(data.get('age', 30))
        emp_status = data.get('employment_status', 'Employed')
        years_emp = int(data.get('years_of_employment', 5))
        bank_balance = float(data.get('bank_balance', 0))
        prev_defaults = int(data.get('previous_defaults', 0))

        # Calculate derived features
        dti_ratio = (existing_emis * 12) / income if income > 0 else 0
        ltv_ratio = loan_amount / collateral_value if collateral_value > 0 else 1.0
        emp_encoded = 2 if emp_status == 'Employed' else (1 if emp_status == 'Self-Employed' else 0)

        # Fraud detection
        fraud_flags = detect_fraud({
            'credit_score': credit_score, 'income_annum': income,
            'loan_amount': loan_amount, 'age': age,
            'bank_balance': bank_balance, 'previous_defaults': prev_defaults
        })

        if USE_RISK_MODEL:
            features = pd.DataFrame([{
                'credit_score': credit_score, 'income_annum': income,
                'loan_amount': loan_amount, 'loan_term': loan_term,
                'existing_loans': existing_loans, 'existing_emis': existing_emis,
                'dti_ratio': dti_ratio, 'collateral_value': collateral_value,
                'ltv_ratio': ltv_ratio, 'age': age,
                'employment_encoded': emp_encoded, 'years_of_employment': years_emp,
                'bank_balance': bank_balance, 'previous_defaults': prev_defaults
            }])
            features = features.reindex(columns=risk_columns, fill_value=0)
            scaled = risk_scaler.transform(features)
            probs = risk_model.predict_proba(scaled)[0]  # [P(Low), P(Medium), P(High)]
            risk_score = round(probs[1] * 50 + probs[2] * 100, 1)

            # Feature importances
            importances = risk_model.feature_importances_
            top_idx = np.argsort(importances)[::-1][:5]
            feat_imp = [{"feature": risk_columns[i], "importance": round(importances[i]*100, 1)} for i in top_idx]
        else:
            # Fallback to old model
            input_df = pd.DataFrame([{
                'credit_score': credit_score, 'income_annum': income,
                'loan_amount': loan_amount, 'loan_term': loan_term
            }])
            input_df = input_df.reindex(columns=old_columns, fill_value=0)
            scaled = old_scaler.transform(input_df)
            pred = old_model.predict(scaled)[0]
            risk_score = 25.0 if pred == 1 else 75.0
            feat_imp = []

        # Classify risk
        if risk_score <= 30:
            risk_level = "Low Risk"
            prediction = "Approved"
        elif risk_score <= 60:
            risk_level = "Medium Risk"
            prediction = "Approved"
        else:
            risk_level = "High Risk"
            prediction = "Rejected"

        # Override with fraud
        if len(fraud_flags) >= 2:
            risk_level = "High Risk"
            prediction = "Rejected"
            risk_score = max(risk_score, 80)

        # EMI and Interest Calculation
        interest_rate = get_interest_rate(risk_score)
        emi = calculate_emi(loan_amount, interest_rate, loan_term)
        total_payment = emi * loan_term
        total_interest = round(total_payment - loan_amount, 2)

        # Explanations
        explanations = get_risk_explanation({
            'credit_score': credit_score, 'dti_ratio': dti_ratio,
            'ltv_ratio': ltv_ratio, 'previous_defaults': prev_defaults,
            'employment_status': emp_status
        }, risk_score, feat_imp)

        # Save full applications to DB
        is_full = data.get('name') and data.get('email')
        app_type = 'full' if is_full else 'quick'

        if is_full:
            try:
                conn = get_db()
                if conn:
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO loan_applications
                        (credit_score, income_annum, loan_amount, loan_term,
                         existing_loans, existing_emis, dti_ratio, collateral_value,
                         ltv_ratio, bank_balance, previous_defaults, age,
                         employment_status, years_of_employment,
                         name, email, phone, gender,
                         prediction_result, risk_score, risk_level, emi_amount,
                         fraud_flags, feature_importance, application_type,
                         interest_rate, total_interest)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (
                        credit_score, income, loan_amount, loan_term,
                        existing_loans, existing_emis, dti_ratio, collateral_value,
                        ltv_ratio, bank_balance, prev_defaults, age,
                        emp_status, years_emp,
                        data.get('name'), data.get('email'), data.get('phone'), data.get('gender'),
                        prediction, risk_score, risk_level, emi,
                        json.dumps(fraud_flags), json.dumps(feat_imp), app_type,
                        interest_rate, total_interest
                    ))
                    conn.commit()
                    cur.close()
            except Exception as e:
                print(f"DB insert error: {e}")

        return jsonify({
            "status": prediction,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "emi": emi,
            "interest_rate": interest_rate,
            "total_interest": total_interest,
            "dti_ratio": round(dti_ratio, 4),
            "ltv_ratio": round(ltv_ratio, 4),
            "fraud_flags": fraud_flags,
            "explanations": explanations,
            "feature_importance": feat_imp
        })

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/api/predict', methods=['POST'])
def api_predict():
    """External API endpoint — same logic, JSON in/out."""
    return predict()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('admin'):
        return redirect(url_for('dashboard'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            log_admin_action('login', 'Successful login')
            return redirect(url_for('dashboard'))
        else:
            log_admin_action('login_failed', f'Failed login attempt: {username}')
            error = "Invalid username or password."
    return render_template('login.html', error=error)


@app.route('/dashboard')
@login_required
def dashboard():
    log_admin_action('view_dashboard')

    # Get filter/search params
    search = request.args.get('search', '').strip()
    risk_filter = request.args.get('risk', 'all')
    sort_by = request.args.get('sort', 'created_at')
    sort_dir = request.args.get('dir', 'DESC')

    stats = {
        'total_applications': 0, 'approved_count': 0, 'rejected_count': 0,
        'avg_income': 0, 'avg_loan_amount': 0, 'max_credit': 0, 'min_credit': 0,
        'employment_data': [], 'risk_data': [], 'recent_applications': [],
        'search': search, 'risk_filter': risk_filter, 'sort_by': sort_by, 'sort_dir': sort_dir
    }

    try:
        conn = get_db()
        if not conn:
            return render_template('dashboard.html', stats=stats)
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT COUNT(*) as total FROM loan_applications")
        stats['total_applications'] = (cur.fetchone() or {}).get('total', 0)

        cur.execute("SELECT prediction_result, COUNT(*) as cnt FROM loan_applications GROUP BY prediction_result")
        for r in cur.fetchall():
            if r['prediction_result'] == 'Approved':
                stats['approved_count'] = r['cnt']
            elif r['prediction_result'] == 'Rejected':
                stats['rejected_count'] = r['cnt']

        cur.execute("SELECT AVG(income_annum) as v FROM loan_applications")
        v = (cur.fetchone() or {}).get('v')
        stats['avg_income'] = round(v, 2) if v else 0

        cur.execute("SELECT AVG(loan_amount) as v FROM loan_applications")
        v = (cur.fetchone() or {}).get('v')
        stats['avg_loan_amount'] = round(v, 2) if v else 0

        cur.execute("SELECT employment_status, COUNT(*) as cnt FROM loan_applications GROUP BY employment_status")
        stats['employment_data'] = cur.fetchall()

        cur.execute("SELECT MAX(credit_score) as mx, MIN(credit_score) as mn FROM loan_applications")
        r = cur.fetchone() or {}
        stats['max_credit'] = r.get('mx') or 0
        stats['min_credit'] = r.get('mn') or 0

        cur.execute("SELECT risk_level, COUNT(*) as cnt FROM loan_applications GROUP BY risk_level")
        stats['risk_data'] = [r for r in cur.fetchall() if r['risk_level']]

        # Filtered + searched applications
        where_clauses = []
        params = []
        if search:
            where_clauses.append("(name LIKE %s OR email LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])
        if risk_filter and risk_filter != 'all':
            where_clauses.append("risk_level = %s")
            params.append(risk_filter)

        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        # Validate sort column
        allowed_sorts = {'created_at', 'risk_score', 'loan_amount', 'credit_score', 'income_annum'}
        if sort_by not in allowed_sorts:
            sort_by = 'created_at'
        if sort_dir not in ('ASC', 'DESC'):
            sort_dir = 'DESC'

        cur.execute(f"""
            SELECT * FROM loan_applications {where_sql}
            ORDER BY {sort_by} {sort_dir} LIMIT 50
        """, params)
        recent = cur.fetchall()
        for row in recent:
            if not row.get('risk_level') or row.get('risk_level') == '-':
                risk = row.get('risk_score', 0)
                if risk <= 30:
                    row['risk_level'] = "Low Risk"
                elif risk <= 60:
                    row['risk_level'] = "Medium Risk"
                else:
                    row['risk_level'] = "High Risk"
        stats['recent_applications'] = recent
        cur.close()
    except Exception as e:
        print(f"Dashboard error: {e}")

    return render_template('dashboard.html', stats=stats)


@app.route('/application/<int:app_id>')
@login_required
def get_application(app_id):
    """Return full application details as JSON (for modal view)."""
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM loan_applications WHERE id = %s", (app_id,))
        app_data = cur.fetchone()
        cur.close()
        if app_data:
            app_data['created_at'] = str(app_data['created_at'])
            return jsonify(app_data)
        return jsonify({"error": "Not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/export-csv')
@login_required
def export_csv():
    """Export all applications as CSV download."""
    log_admin_action('export_csv', 'Exported application data')
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM loan_applications ORDER BY created_at DESC")
        rows = cur.fetchall()
        cur.close()

        if not rows:
            return "No data to export", 404

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in rows:
            row['created_at'] = str(row.get('created_at', ''))
            writer.writerow(row)

        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={"Content-Disposition": "attachment;filename=loan_applications.csv"}
        )
    except Exception as e:
        return str(e), 500


@app.route('/logout')
def logout():
    log_admin_action('logout')
    session.pop('admin', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)