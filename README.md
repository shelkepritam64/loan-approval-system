# 🏦 Smart Loan Risk Assessment System

An AI-powered Banking Loan Risk Assessment System that helps evaluate loan applications using Machine Learning, financial risk analysis, EMI calculations, and real-time dashboard analytics.

---

## 🚀 Project Overview

Traditional loan approval processes are often time-consuming and depend heavily on manual review. This project simulates a real-world banking loan assessment system by combining:

- Machine Learning (Random Forest)
- Financial Risk Analysis
- Loan Approval Prediction
- EMI & Interest Calculation
- MySQL Database Management
- Admin Analytics Dashboard

The system evaluates an applicant's financial profile and predicts their loan risk level while providing explainable insights into the decision.

---

## ✨ Features

### 👤 User Module

#### Quick Prediction
- Credit Score
- Annual Income
- Loan Amount
- Loan Term
- Employment Status

#### Full Application
- Personal Information
- Financial History
- Collateral Information
- Previous Defaults
- Bank Balance
- Employment Details

### 🤖 AI Risk Assessment

The system calculates:

- Risk Score (0–100%)
- Risk Level:
  - 🟢 Low Risk
  - 🟡 Medium Risk
  - 🔴 High Risk
- Loan Recommendation
- Key Decision Factors

---

## 💰 Financial Calculations

### EMI Calculation

Monthly EMI is calculated using standard banking formulas.

### Interest Calculation

Interest rates are assigned dynamically based on risk:

| Risk Level | Interest Rate |
|------------|--------------|
| Low Risk | 8% |
| Medium Risk | 10% |
| High Risk | 14% |

### Additional Metrics

- Debt-to-Income Ratio (DTI)
- Loan-to-Value Ratio (LTV)
- Total Interest Payable

---

## 🧠 Machine Learning Model

### Algorithm Used

- Random Forest Classifier

### Feature Engineering

The model uses:

- Credit Score
- Income
- Loan Amount
- Loan Term
- Existing Loans
- Existing EMIs
- DTI Ratio
- Collateral Value
- LTV Ratio
- Bank Balance
- Previous Defaults
- Employment Status
- Age
- Years of Employment

### Model Outputs

- Risk Score
- Risk Level
- Loan Decision

---

## 📊 Admin Dashboard

Secure admin panel with analytics and reporting.

### Dashboard Features

- Total Applications
- Approved Applications
- Rejected Applications
- Average Income
- Average Loan Amount
- Risk Distribution
- Approval vs Rejection Analysis
- Employment Distribution
- CSV Export

### SQL Concepts Demonstrated

- COUNT()
- AVG()
- GROUP BY
- ORDER BY
- CASE Statements
- Filtering & Search

---

## 🗄️ Database

### Database: MySQL

Table: `loan_applications`

Stores:

- Applicant Information
- Financial Information
- Risk Metrics
- Prediction Results
- EMI Details
- Interest Calculations

---

## 🛠️ Technology Stack

### Frontend
- HTML5
- CSS3
- JavaScript

### Backend
- Flask (Python)

### Database
- MySQL

### Machine Learning
- Scikit-Learn
- Random Forest

### Data Processing
- Pandas
- NumPy

### Visualization
- Chart.js

### Version Control
- Git
- GitHub

---

## 📂 Project Structure

```text
Smart-Loan-Risk-Assessment-System/
│
├── Backend/
│   ├── app.py
│   ├── risk_model.pkl
│   ├── scaler.pkl
│   ├── columns.pkl
│   └── train_model.py
│
├── Frontend/
│   ├── index.html
│   ├── admin.html
│   ├── style.css
│   └── script.js
│
├── Database/
│   └── loan_system.sql
│
├── README.md
└── requirements.txt
```

---

## ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/shelkepritam64/loan-approval-system.git
```

### Navigate to Project

```bash
cd loan-approval-system
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Flask Application

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

---

## 🔐 Admin Credentials

```text
Username: admin@123
Password: ad@123
```

---

## 📈 Future Enhancements

- Real Bank API Integration
- Fraud Detection Module
- Credit Bureau Integration
- Email/SMS Notifications
- Cloud Deployment
- Advanced Risk Analytics
- Explainable AI Dashboard

---

## 🎯 Learning Outcomes

This project demonstrates:

- Machine Learning in Banking
- Credit Risk Assessment
- Financial Data Analysis
- Full-Stack Web Development
- Database Design & SQL
- Model Deployment using Flask

---

## 👨‍💻 Developer

**Pritam Shelke**

Smart Loan Risk Assessment System

Banking Risk Analysis & Loan Decision Support Platform

---

## ⭐ Project Highlights

✅ Random Forest Risk Prediction  
✅ EMI & Interest Calculation  
✅ Explainable AI Decisions  
✅ Admin Analytics Dashboard  
✅ MySQL Database Integration  
✅ Flask Backend API  
✅ Professional Banking UI  
✅ GitHub Version Controlled
