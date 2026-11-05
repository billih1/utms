from django import forms
from .models import Route, Van


class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = ['route_name', 'rent', 'description', 'is_active']
        widgets = {
            'route_name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'e.g. Daska - GCUF'}),
            'rent': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': '5000'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'rows': 3, 'placeholder': 'Optional stops/notes'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500'}),
        }


class VanForm(forms.ModelForm):
    class Meta:
        model = Van
        fields = ['van_number', 'capacity', 'route', 'is_active']
        widgets = {
            'van_number': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'e.g. LEA-101'}),
            'capacity': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': '22'}),
            'route': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500'}),
        }

    def clean_capacity(self):
        capacity = self.cleaned_data.get('capacity')
        if capacity and (capacity < 1 or capacity > 100):
            raise forms.ValidationError("Capacity must be between 1 and 100.")
        return capacity
