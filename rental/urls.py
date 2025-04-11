from django.urls import path
from .views import car_list, rent_car, process_payment, payment_success, payment_history, car_detail, add_review, car_availability, dashboard, manage_cars, manage_car, delete_car
from . import views

urlpatterns = [
    path('', views.car_list, name='car_list'),
    path('car/<int:car_id>/', views.car_detail, name='car_detail'),
    path('rent/<int:car_id>/', views.rent_car, name='rent_car'),
    path('payment/<int:payment_id>/', views.process_payment, name='process_payment'),
    path('payment/success/<int:payment_id>/', views.payment_success, name='payment_success'),
    path('payment/history/', views.payment_history, name='payment_history'),
    path('review/<int:car_id>/', views.add_review, name='add_review'),
    path('car/<int:car_id>/availability/', views.car_availability, name='car_availability'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('manage-cars/', views.manage_cars, name='manage_cars'),
    path('manage-car/', views.manage_car, name='manage_car'),
    path('manage-car/<int:car_id>/', views.manage_car, name='manage_car'),
    path('delete-car/<int:car_id>/', views.delete_car, name='delete_car'),
]
