# University Transport Management System (UTMS) with AI-Based Defaulter Prediction

[![Django](https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.8-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Vercel](https://img.shields.io/badge/Vercel-Deploy_Ready-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com/)

**Project Code:** `TMS-FYP-2026`  
**Institution:** Government College University Faisalabad (GCUF) &bull; Department of Information Technology  
**Software Engineering Standards:** IEEE 830-1998 & ISO/IEC/IEEE 29148:2018  

---

## 📖 Executive Summary
The **University Transport Management System (UTMS)** is an enterprise web application designed to digitize university fleet operations, enforce strict passenger capacity controls (20–22 seats per van), automate student monthly dues reconciliation with the National Bank of Pakistan (NBP), issue tamper-verifiable 3-part deposit challans with standalone QR codes, and leverage a Scikit-Learn Logistic Regression Machine Learning engine to predict upcoming student fee defaults before penalties accrue.

---

## ✨ Key System Capabilities

### 1. 🚌 Fleet & Seat Allocation Engine
- **Strict Capacity Overfill Blocking:** Enforces hard limits (20–22 passengers) per van. Attempting to assign a student to a full van triggers a validation error with prompt recommendation to allocate a standby spare vehicle.
- **Standby Spare Vehicle Support:** Unallocated reserve vans automatically step in to handle route overflow during peak academic sessions.
- **Designated Routes & Fixed Monthly Rents:** Centralized route tariffs with automated rent calculation.

### 2. 💳 Financial Reconciliations & Document Engine
- **Automated Monthly Dues Batch Generation:** Automatically evaluates all active enrolled students and generates their monthly transport dues in an atomic database transaction.
- **Standardized 3-Part Bank Deposit Challans:** Printable PDF/HTML deposit slips containing **Bank Copy**, **Accounts Office Copy**, and **Student Copy** tailored for National Bank of Pakistan (NBP Main Campus, Faisalabad).
- **Embedded Verifiable QR Codes:** Each challan and fee voucher includes an offline-scannable QR code embedding structured JSON metadata for instant gate and teller verification.
- **Fee Clearance Receipts:** Generates official stamped clearance receipts with a breakdown of remaining dues upon payment recording.
- **Bulk Printing:** Supports 1-click batch printing of all monthly challans and vouchers.
- **Roster Auto-Import:** Upload Excel (`.xlsx`) or CSV rosters to batch import/update student registrations.

### 3. 🤖 AI Defaulter Prediction Engine (Scikit-Learn)
- **Predictive Target:** Binary classification of payment default probability for the target upcoming calendar month.
- **Feature Vector:** Consecutive unpaid months, lifetime settlement ratio, route rent amount, student seniority semester, and payment timing delinquency.
- **Risk Tiers:**
  - **High Risk ($\ge 70\%$):** Severe default probability triggering immediate administrative follow-up.
  - **Medium Risk ($40\% - 69\%$):** Automated reminder SMS/notice.
  - **Low Risk ($< 40\%$):** Prompt historical payer.
- **Human-Readable Model Explanations:** Every prediction is stored with human-auditable rationale (e.g., *"3 consecutive unpaid months; historical settlement ratio 0.45"*).

### 4. 📋 Operations & Gate Dispatch
- **Driver Trip Panel:** Mobile-friendly driver interface to log departure, arrival, and vehicle operational status (*Scheduled*, *Departed*, *On Route*, *Arrived*, *Off*).
- **Vehicle Entry Log:** Real-time campus gate audit feed recording all incoming and outgoing university fleet vehicles.

---

## 👥 Role-Based Access Control (RBAC) & Demo Accounts

The system implements 4 distinct portals governed by role checks and automatic 30-minute idle session timeouts:

| Role | Username | Password | Key Responsibilities |
|---|---|---|---|
| **Admin** | `admin` | `admin123` | System oversight, student/route/van CRUD, capacity assignment, AI predictions, all reports. |
| **Accountant** | `accountant` | `accountant123` | Dues batch generation, NBP challans, payment settlement, clearance receipts, bulk print. |
| **Driver** | `driver` | `driver123` | Gate arrival/departure timestamp logging, route status updates. |
| **Student** | `student` | `student123` | View assigned route and van, inspect payment ledger, download 3-part bank deposit challans. |

---

## 🛠️ Technology Stack
- **Backend:** Python 3.11, Django 5.2 (CBVs, ORM, Form Validation, Auth, CSRF)
- **Frontend:** Tailwind CSS (Institutional UI styled after Pakistani educational boards), Alpine.js, HTMX 2.0, Chart.js, Lucide Icons
- **Machine Learning:** Scikit-Learn 1.8, Pandas, NumPy, Joblib
- **Document Processing:** ReportLab, Pillow, Python QrCode, OpenPyXL
- **Static Assets:** WhiteNoise with compressed manifest storage
- **Deployment:** Vercel Serverless WSGI (`@vercel/python`) / Gunicorn

---

## 🚀 Local Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/billih1/utms.git
cd utms

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate    # Linux / macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run database migrations
python manage.py migrate

# 5. Seed initial demo data (Routes, Vans, Students, Demo Users, ML Model)
python seed_demo_data.py

# 6. Run development server
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## 🧪 Automated Test Suite

The project includes an end-to-end automated test suite verifying all 25 Functional Requirements (FR-01 to FR-25):

```bash
python manage.py test tests_srs transport students accounts finance operations reports ai_predictor
```
*Result: 55 unit and integration tests passing in ~4 seconds.*

---

## 🌐 Deploying to Vercel

The repository is pre-configured with `vercel.json`, `build_files.sh`, and a Vercel-ready `tms/wsgi.py`.

1. Push this repository to your GitHub account (`https://github.com/billih1/utms`).
2. Log in to [Vercel](https://vercel.com/) and click **"Add New Project"**.
3. Select **"Import Git Repository"** and choose `billih1/utms`.
4. Leave the default settings (Vercel automatically detects `vercel.json` and runs `build_files.sh`).
5. Click **Deploy**. Your system will be live on `https://utms.vercel.app`!
