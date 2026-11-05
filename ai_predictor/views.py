from django.shortcuts import render
from django.contrib import messages
from django.utils import timezone
from accounts.decorators import accountant_required
from .models import Prediction
from .model import run_prediction_for_month, train_defaulter_model


@accountant_required
def ai_insights_view(request):
    """
    FR-22 / UC-21: AI Insights view for Defaulter Prediction.
    """
    current_next_month = timezone.now().strftime("%b %Y")
    selected_month = request.POST.get('target_month', current_next_month).strip()

    predictions = []
    trained_status = None

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'train':
            trained_status = train_defaulter_model()
            if trained_status.get('success'):
                messages.success(request, f"Defaulter prediction ML model trained successfully with {trained_status['samples']} samples.")
            else:
                messages.info(request, f"ML note: {trained_status.get('reason')}")

        # Run predictions
        predictions = run_prediction_for_month(selected_month)
        messages.success(request, f"Defaulter prediction completed for {selected_month}. {len(predictions)} students evaluated.")
    else:
        # Load existing if available
        predictions = Prediction.objects.filter(target_month=selected_month).select_related('student', 'student__route')

    # Counts
    high_count = sum(1 for p in predictions if p.risk_level == 'High')
    med_count = sum(1 for p in predictions if p.risk_level == 'Medium')
    low_count = sum(1 for p in predictions if p.risk_level == 'Low')

    return render(request, 'ai_predictor/insights.html', {
        'target_month': selected_month,
        'predictions': predictions,
        'high_count': high_count,
        'med_count': med_count,
        'low_count': low_count,
        'trained_status': trained_status,
    })
