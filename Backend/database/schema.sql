-- =============================================
-- Banking Loan Risk Assessment System — Schema
-- =============================================

CREATE DATABASE IF NOT EXISTS loan_system;
USE loan_system;

-- Enhanced loan applications table
CREATE TABLE IF NOT EXISTS loan_applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- Financial Info
    credit_score FLOAT,
    income_annum FLOAT,
    loan_amount FLOAT,
    loan_term FLOAT,
    existing_loans INT DEFAULT 0,
    existing_emis FLOAT DEFAULT 0,
    dti_ratio FLOAT DEFAULT 0,
    collateral_value FLOAT DEFAULT 0,
    ltv_ratio FLOAT DEFAULT 0,
    bank_balance FLOAT DEFAULT 0,
    previous_defaults INT DEFAULT 0,
    -- Personal Info
    age INT DEFAULT 0,
    employment_status VARCHAR(50),
    years_of_employment INT DEFAULT 0,
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(20),
    gender VARCHAR(20),
    -- Prediction Results
    prediction_result VARCHAR(20),
    risk_score FLOAT DEFAULT 0,
    risk_level VARCHAR(20),
    emi_amount FLOAT DEFAULT 0,
    fraud_flags TEXT,
    feature_importance TEXT,
    -- Metadata
    application_type VARCHAR(20) DEFAULT 'quick',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Indexes
    INDEX idx_risk_score (risk_score),
    INDEX idx_prediction (prediction_result),
    INDEX idx_employment (employment_status),
    INDEX idx_created (created_at),
    INDEX idx_risk_level (risk_level)
);

-- Admin activity logs
CREATE TABLE IF NOT EXISTS admin_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_username VARCHAR(100),
    action VARCHAR(100),
    ip_address VARCHAR(50),
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_admin_created (created_at)
);
