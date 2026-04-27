/* =============================================
   Banking Loan Risk Assessment — Main JS
   ============================================= */

let currentTab = 'quick';

function switchTab(tab) {
  currentTab = tab;
  document.getElementById('tab-quick').classList.toggle('active', tab === 'quick');
  document.getElementById('tab-full').classList.toggle('active', tab === 'full');
  document.getElementById('extendedFields').classList.toggle('show', tab === 'full');
  hideResult();
  clearValidation();
}

function hideResult() {
  document.getElementById('resultPanel').style.display = 'none';
}

function clearValidation() {
  document.querySelectorAll('.form-group').forEach(g => g.classList.remove('invalid'));
}

function showError(id) {
  const el = document.getElementById(id);
  if (el) el.closest('.form-group').classList.add('invalid');
}

function validate() {
  clearValidation();
  let ok = true;
  const cs = +document.getElementById('credit_score').value;
  if (!cs || cs < 300 || cs > 900) { showError('credit_score'); ok = false; }

  const inc = +document.getElementById('income_annum').value;
  if (!document.getElementById('income_annum').value || inc < 0) { showError('income_annum'); ok = false; }

  const la = +document.getElementById('loan_amount').value;
  if (!la || la < 1) { showError('loan_amount'); ok = false; }

  if (!document.getElementById('employment_status').value) { showError('employment_status'); ok = false; }

  const lt = +document.getElementById('loan_term').value;
  if (!lt || lt < 1 || lt > 480) { showError('loan_term'); ok = false; }

  if (currentTab === 'full') {
    if (!document.getElementById('name').value.trim()) { showError('name'); ok = false; }
    const em = document.getElementById('email').value.trim();
    if (!em || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(em)) { showError('email'); ok = false; }
    if (!document.getElementById('phone').value.trim()) { showError('phone'); ok = false; }
  }
  return ok;
}

function getVal(id, def) {
  const el = document.getElementById(id);
  return el && el.value ? +el.value : def;
}

// ===== Form Submission =====
document.getElementById('loanForm').addEventListener('submit', async function(e) {
  e.preventDefault();
  if (!validate()) return;

  const btn = document.getElementById('predictBtn');
  btn.classList.add('loading');
  btn.disabled = true;
  hideResult();

  const payload = {
    credit_score: +document.getElementById('credit_score').value,
    income_annum: +document.getElementById('income_annum').value,
    loan_amount: +document.getElementById('loan_amount').value,
    employment_status: document.getElementById('employment_status').value,
    loan_term: +document.getElementById('loan_term').value
  };

  if (currentTab === 'full') {
    payload.age = getVal('age', 30);
    payload.years_of_employment = getVal('years_of_employment', 5);
    payload.existing_loans = getVal('existing_loans', 0);
    payload.existing_emis = getVal('existing_emis', 0);
    payload.bank_balance = getVal('bank_balance', 0);
    payload.previous_defaults = getVal('previous_defaults', 0);
    payload.collateral_value = getVal('collateral_value', 0);
    payload.name = document.getElementById('name').value.trim();
    payload.email = document.getElementById('email').value.trim();
    payload.phone = document.getElementById('phone').value.trim();
    payload.gender = document.getElementById('gender').value || '';
  }

  try {
    const res = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    showResult(data);
  } catch (err) {
    showErrorResult();
  } finally {
    btn.classList.remove('loading');
    btn.disabled = false;
  }
});

function showErrorResult() {
  const panel = document.getElementById('resultPanel');
  panel.style.display = 'block';
  document.getElementById('gaugeText').textContent = 'ERR';
  document.getElementById('gaugeArc').setAttribute('stroke-dasharray', '0 251');
  document.getElementById('decisionBadge').className = 'decision-badge high';
  document.getElementById('decisionBadge').textContent = 'Connection Error';
  document.getElementById('decisionLabel').textContent = 'Make sure the backend server is running.';
}

function showResult(data) {
  if (data.error) { showErrorResult(); return; }

  const panel = document.getElementById('resultPanel');
  panel.style.display = 'block';

  // Risk Gauge
  const score = data.risk_score || 0;
  const arcLen = (score / 100) * 251; // 251 is the arc circumference
  const gaugeArc = document.getElementById('gaugeArc');
  const gaugeText = document.getElementById('gaugeText');

  // Animate after a small delay
  setTimeout(() => {
    gaugeArc.setAttribute('stroke-dasharray', arcLen + ' 251');
    gaugeText.textContent = score + '%';
  }, 100);

  // Decision Badge
  const badge = document.getElementById('decisionBadge');
  const label = document.getElementById('decisionLabel');

  if (data.risk_level === 'Low Risk' || data.risk_score <= 30) {
    badge.className = 'decision-badge low';
    badge.textContent = 'LOW RISK - Loan Likely to be Approved';
    label.textContent = 'Strong financial profile detected.';
  } else if (data.risk_level === 'Medium Risk' || data.risk_score <= 60) {
    badge.className = 'decision-badge medium';
    badge.textContent = 'MEDIUM RISK - Review Recommended';
    label.textContent = 'Some risk factors present. Manual review advised.';
  } else {
    badge.className = 'decision-badge high';
    badge.textContent = 'HIGH RISK - Loan Likely to be Rejected';
    label.textContent = 'Multiple risk factors identified.';
  }

  // Info Cards
  document.getElementById('emiValue').textContent = '₹' + Number(data.emi || 0).toLocaleString();
  document.getElementById('interestRateValue').textContent = (data.interest_rate || 0) + '%';
  document.getElementById('totalInterestValue').textContent = '₹' + Number(data.total_interest || 0).toLocaleString();
  document.getElementById('dtiValue').textContent = ((data.dti_ratio || 0) * 100).toFixed(1) + '%';
  document.getElementById('ltvValue').textContent = ((data.ltv_ratio || 0) * 100).toFixed(1) + '%';

  // Fraud Flags
  const fraudSection = document.getElementById('fraudSection');
  const fraudList = document.getElementById('fraudList');
  if (data.fraud_flags && data.fraud_flags.length > 0) {
    fraudSection.style.display = 'block';
    fraudList.innerHTML = data.fraud_flags.map(f => '<li>' + f + '</li>').join('');
  } else {
    fraudSection.style.display = 'none';
  }

  // Explanations
  const expList = document.getElementById('explanationList');
  if (data.explanations && data.explanations.length > 0) {
    expList.innerHTML = data.explanations.map(e => `
      <div class="explanation-item">
        <div class="exp-indicator ${e.impact}"></div>
        <div>
          <div class="exp-factor">${e.factor}</div>
          <div class="exp-detail">${e.detail}</div>
        </div>
      </div>
    `).join('');
  } else {
    expList.innerHTML = '';
  }

  // Feature Importance
  const featSection = document.getElementById('featSection');
  const featBars = document.getElementById('featBars');
  if (data.feature_importance && data.feature_importance.length > 0) {
    featSection.style.display = 'block';
    const maxImp = Math.max(...data.feature_importance.map(f => f.importance));
    featBars.innerHTML = data.feature_importance.map(f => {
      const pct = (f.importance / maxImp * 100).toFixed(0);
      const name = f.feature.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
      return `
        <div class="feat-bar-item">
          <span class="feat-bar-label">${name}</span>
          <div class="feat-bar-track"><div class="feat-bar-fill" style="width:0%"></div></div>
          <span class="feat-bar-val">${f.importance}%</span>
        </div>`;
    }).join('');
    // Animate bars
    setTimeout(() => {
      const fills = featBars.querySelectorAll('.feat-bar-fill');
      data.feature_importance.forEach((f, i) => {
        if (fills[i]) fills[i].style.width = (f.importance / maxImp * 100).toFixed(0) + '%';
      });
    }, 200);
  } else {
    featSection.style.display = 'none';
  }

  // Scroll to result
  panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
