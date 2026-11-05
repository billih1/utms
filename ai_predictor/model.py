import os
import joblib
import numpy as np
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from django.conf import settings
from students.models import Student
from finance.models import FeePayment
from .models import Prediction
from .features import extract_student_features

MODEL_DIR = settings.BASE_DIR / 'ml_models'
MODEL_PATH = MODEL_DIR / 'defaulter_model.joblib'


def train_defaulter_model():
    """
    Trains a Logistic Regression pipeline using historical payment records.
    Returns training status dict.
    """
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    students = Student.objects.filter(fee_payments__isnull=False).distinct()
    X = []
    y = []

    for s in students:
        payments = s.fee_payments.all().order_by('created_at')
        if payments.count() < 2:
            continue

        # Use historical features up to second-to-last payment to predict last payment status
        last_payment = payments.last()
        features = extract_student_features(s)
        feature_vector = [
            features['total_months'],
            features['paid_months'],
            features['unpaid_months'],
            features['payment_ratio'],
            features['consecutive_defaults'],
            features['route_rent'],
            features['semester_num'],
        ]
        label = 1 if last_payment.status == 'Unpaid' else 0
        X.append(feature_vector)
        y.append(label)

    # Need at least a few samples with both classes to fit a logistic model
    if len(X) >= 6 and len(set(y)) > 1:
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('clf', LogisticRegression(random_state=42))
        ])
        pipeline.fit(np.array(X), np.array(y))
        joblib.dump(pipeline, MODEL_PATH)
        return {'success': True, 'samples': len(X), 'model': 'LogisticRegression'}

    return {'success': False, 'samples': len(X), 'reason': 'Insufficient historical variations for ML fit; heuristic engine active.'}


def run_prediction_for_month(target_month: str) -> list:
    """
    Runs prediction for all active students assigned to a transport route.
    Saves Prediction instances and returns summary list.
    """
    active_students = Student.objects.filter(is_active=True, route__isnull=False).select_related('route')

    model = None
    if MODEL_PATH.exists():
        try:
            model = joblib.load(MODEL_PATH)
        except Exception:
            model = None

    results = []

    for s in active_students:
        feat = extract_student_features(s)
        feat_vector = [
            feat['total_months'],
            feat['paid_months'],
            feat['unpaid_months'],
            feat['payment_ratio'],
            feat['consecutive_defaults'],
            feat['route_rent'],
            feat['semester_num'],
        ]

        if model is not None:
            try:
                prob = float(model.predict_proba([feat_vector])[0][1])
            except Exception:
                prob = None
        else:
            prob = None

        # Heuristic calculation if ML model not yet trained
        if prob is None:
            if feat['consecutive_defaults'] >= 3 or feat['payment_ratio'] < 0.4:
                prob = 0.85
            elif feat['consecutive_defaults'] >= 1 or feat['payment_ratio'] < 0.75:
                prob = 0.55
            elif feat['unpaid_months'] > 0:
                prob = 0.35
            else:
                prob = 0.12

        # Assign Risk Level
        if prob >= 0.70:
            risk_level = Prediction.RiskLevel.HIGH
        elif prob >= 0.40:
            risk_level = Prediction.RiskLevel.MEDIUM
        else:
            risk_level = Prediction.RiskLevel.LOW

        # Human-readable justification (Figure 20 of SRS)
        if feat['consecutive_defaults'] >= 2:
            reason = f"{feat['consecutive_defaults']} consecutive unpaid months"
        elif feat['unpaid_months'] >= 1:
            reason = f"{feat['unpaid_months']} unpaid month in history"
        elif feat['total_months'] == 0:
            reason = "New transport registration (no history)"
        else:
            reason = "Consistent timely payment record"

        pred_obj, _ = Prediction.objects.update_or_create(
            student=s,
            target_month=target_month,
            defaults={
                'risk_score': prob,
                'risk_level': risk_level,
                'features_json': feat,
                'reason': reason,
            }
        )
        results.append(pred_obj)

    # Sort high risk first
    results.sort(key=lambda x: x.risk_score, reverse=True)
    return results
