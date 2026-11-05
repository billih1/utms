from django import forms
from django.utils import timezone
from .models import FeePayment


def get_month_choices():
    choices = []
    now = timezone.now()
    # Current month and previous 11 months
    for i in range(12):
        # Approximate month offset
        month_year = (now.replace(day=1) - timezone.timedelta(days=i * 28)).strftime("%b %Y")
        if (month_year, month_year) not in choices:
            choices.append((month_year, month_year))
    return choices


class GenerateDuesForm(forms.Form):
    month = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'e.g. Nov 2026'
        }),
        help_text="Format: 'Month Year' (e.g. Nov 2026)"
    )


class PaymentRecordForm(forms.Form):
    amount_paid = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'rows': 2,
            'placeholder': 'Optional bank transaction or receipt notes'
        })
    )
