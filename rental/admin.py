from django.contrib import admin
from .models import Car, Customer, Rental , Payment


admin.site.register(Car)
admin.site.register(Customer)
admin.site.register(Rental)
admin.site.register(Payment)
