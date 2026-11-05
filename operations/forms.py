from django import forms
from .models import VehicleLog
from transport.models import Van, Route


class DriverLogForm(forms.ModelForm):
    class Meta:
        model = VehicleLog
        fields = ['van', 'route', 'departure_time', 'arrival_time', 'status', 'notes']
        widgets = {
            'van': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white'}),
            'route': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white'}),
            'departure_time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'arrival_time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'status': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white'}),
            'notes': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Optional remarks (e.g. Traffic delay)'}),
        }
