from django import forms
from .models import Car, Location, Rental

class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = [
            'brand', 'model', 'year', 'horsepower', 'color',
            'price_per_day', 'deposit', 'description', 'image',
            'daily_kilometer_limit', 'extra_kilometer_price', 'status',
            'available_locations'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'status': forms.Select(choices=Car._meta.get_field('status').choices),
            'available_locations': forms.Select(choices=[(loc.id, f"{loc.name} - {loc.city}") for loc in Location.objects.all()]),
        } 

class RentalForm(forms.ModelForm):
    class Meta:
        model = Rental
        fields = [
            'car', 'customer', 'start_date', 'end_date', 
            'pickup_location', 'insurance', 'total_price', 'status',
            'created_by', 'notes', 'payment_status'
        ]
        widgets = {
            'status': forms.Select(choices=Rental._meta.get_field('status').choices),
            'payment_status': forms.Select(choices=Rental._meta.get_field('payment_status').choices),
        }


