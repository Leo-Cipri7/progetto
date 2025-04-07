from django.urls import path
from .views import car_list, rent_car, process_payment, payment_success, payment_history, car_detail, add_review, car_availability
from . import views

urlpatterns = [
    path('', car_list, name='car_list'),  
    path('car/<int:car_id>/', car_detail, name='car_detail'),
    path('rent/<int:car_id>/', rent_car, name='rent_car'),
    path('payment/<int:payment_id>/', process_payment, name='process_payment'),
    path('payment/<int:payment_id>/success/', payment_success, name='payment_success'),
    path('payments/', payment_history, name='payment_history'),
    path('car/<int:car_id>/review/', add_review, name='add_review'),
    path('car/<int:car_id>/availability/', car_availability, name='car_availability'),
]
