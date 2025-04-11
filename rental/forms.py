from django import forms
from .models import Car

class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = [
            'brand', 'model', 'year', 'horsepower', 'color',
            'price_per_day', 'deposit', 'description', 'image',
            'daily_kilometer_limit', 'extra_kilometer_price', 'status'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'status': forms.Select(choices=Car._meta.get_field('status').choices),
        } 