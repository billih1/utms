from django import forms
from .models import Student
from transport.models import Route, Van


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['admission_number', 'name', 'program', 'semester', 'phone', 'is_active']
        widgets = {
            'admission_number': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'e.g. 2022-101'}),
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Full Name'}),
            'program': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'BSIT'}),
            'semester': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': '5th'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': '0300-1234567'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500'}),
        }


class StudentAssignForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['route', 'van']
        widgets = {
            'route': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white'}),
            'van': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        van = cleaned_data.get('van')
        route = cleaned_data.get('route')

        if van:
            # Capacity check (TC-05 / FR-07)
            # If student is already assigned to this van, don't count them as extra
            current_count = van.students.filter(is_active=True).exclude(pk=self.instance.pk).count()
            if current_count >= van.capacity:
                raise forms.ValidationError(
                    f"Van '{van.van_number}' is FULL ({current_count}/{van.capacity} seats taken). "
                    "Please choose another van or an available spare vehicle."
                )

            # Check van belongs to selected route or is spare
            if route and van.route and van.route != route:
                raise forms.ValidationError(
                    f"Van '{van.van_number}' belongs to route '{van.route.route_name}', not '{route.route_name}'."
                )

        return cleaned_data
