from django.shortcuts import render, redirect, get_object_or_404
from .models import Car, Customer, Rental, Payment, Review, Insurance, Location, Maintenance, Employee
from django.db.models import Avg, Sum, Count, Q
from datetime import datetime, date, timedelta
from django.db import models
from django.utils import timezone

from django.contrib import messages

from django.contrib.auth.models import User  

from django.db.models.signals import post_save
from django.dispatch import receiver

import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy


def car_list(request):
    # Stampa di debug
    print("Locations available:", Location.objects.all().count())
    
    # Ottieni i parametri di filtro dalla query string
    brand = request.GET.get('brand')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    min_hp = request.GET.get('min_hp')
    location_id = request.GET.get('location')
    
    # Inizia con tutte le auto
    cars = Car.objects.all()
    
    # Applica i filtri
    if brand:
        cars = cars.filter(brand=brand)
    if min_price:
        cars = cars.filter(price_per_day__gte=min_price)
    if max_price:
        cars = cars.filter(price_per_day__lte=max_price)
    if min_hp:
        cars = cars.filter(horsepower__gte=min_hp)
    if location_id:
        cars = cars.filter(available_locations__id=location_id)
    
    # Aggiungi la valutazione media per ogni auto
    for car in cars:
        car.average_rating = Review.objects.filter(car=car).aggregate(Avg('rating'))['rating__avg']
    
    # Ottieni tutte le informazioni disponibili per il filtro
    brands = Car.objects.values_list('brand', flat=True).distinct()
    locations = Location.objects.all()
    
    # Stampa di debug
    print("Locations being sent to template:", [f"{loc.name} - {loc.city}" for loc in locations])
    
    context = {
        'cars': cars,
        'brands': brands,
        'locations': locations,
        'selected_brand': brand,
        'min_price': min_price,
        'max_price': max_price,
        'min_hp': min_hp,
        'selected_location': location_id
    }
    
    return render(request, "rental/car_list.html", context)


def rent_car(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    locations = Location.objects.all()  # Recupera tutte le locations disponibili
    insurances = Insurance.objects.all()  # Recupera tutte le assicurazioni disponibili
    
    # Debug: stampa il numero di assicurazioni trovate
    print(f"Found {insurances.count()} insurance options")
    for insurance in insurances:
        print(f"Insurance: {insurance.name} - {insurance.price_per_day}€/day")
    
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        start_date_str = request.POST.get("start_date")
        end_date_str = request.POST.get("end_date")

        # Convert dates from string to datetime object
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

        # If end date is before start date
        if end_date < start_date:
            messages.error(request, "End date must be after start date.")
            return render(request, "rental/rent_car.html", {"car": car, "error": "End date must be after start date"})

        # Check if car is already rented for selected dates
        overlapping_rentals = Rental.objects.filter(
            car=car,
            end_date__gte=start_date,
            start_date__lte=end_date
        ).exists()

        if overlapping_rentals:
            messages.error(request, "This car is already rented for these dates.")
            return render(request, "rental/rent_car.html", {"car": car, "error": "This car is already rented for these dates."})

        #cerca se l'email è gia associata ad un cliente
        customer, created = Customer.objects.get_or_create(
            email=email,
            defaults={"first_name": first_name, "last_name": last_name}
        )
        #se il cliente esiste non lo crea ma aggiorna le eventuali informazioni
        if not created:
            customer.first_name = first_name
            customer.last_name = last_name
            customer.save()

        insurance_id = request.POST.get("insurance")
        insurance = None
        if insurance_id:
            insurance = get_object_or_404(Insurance, id=insurance_id)

        location_id = request.POST.get('pickup_location')
        location = get_object_or_404(Location, id=location_id)

        # Crea il noleggio
        rental = Rental.objects.create(
            car=car,
            customer=customer,
            insurance=insurance,
            start_date=start_date,
            end_date=end_date,
            pickup_location=location
        )
        
        rental.calculate_total_price()
        rental.save()

        # Crea un record di pagamento in stato "pending"
        payment = Payment.objects.create(
            rental=rental,
            amount=rental.total_price,
            payment_method="Credit Card",  # Default value
            status="pending"
        )
        
        # Redirect alla pagina di pagamento
        return redirect('process_payment', payment_id=payment.id)

    else:
        # Passa le assicurazioni come JSON per il calcolo del prezzo
        insurances_json = {str(insurance.id): float(insurance.price_per_day) for insurance in insurances}
        locations_json = {str(location.id): {
            'address': location.address,
            'opening_hours': location.opening_hours,
            'phone': location.phone
        } for location in locations}
        
        return render(request, 'rental/rent_car.html', {
            'car': car,
            'locations': locations,
            'insurances': insurances,  # Passa le assicurazioni alla template
            'insurances_json': json.dumps(insurances_json),
            'locations_json': json.dumps(locations_json)
        })


def process_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    rental = payment.rental
    
    if request.method == "POST":
        payment_method = request.POST.get("payment_method")
        
        # Aggiorna il metodo di pagamento
        payment.payment_method = payment_method
        
        # Simula il completamento del pagamento
        payment.status = "completed"
        payment.save()
           
        return redirect('payment_success', payment_id=payment.id)
    
    return render(request, 'rental/process_payment.html', {
        'payment': payment,
        'rental': rental
    })


def payment_success(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    rental = payment.rental
    
    return render(request, 'rental/payment_success.html', {
        'payment': payment,
        'rental': rental
    })


def payment_history(request):
    # mostra tutti i pagamenti effettuati (in questo caso di tutta l'app e non del singolo utente)
    payments = Payment.objects.all().order_by('-payment_date')
    
    return render(request, 'rental/payment_history.html', {
        'payments': payments
    })

def add_review(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    
    if request.method == "POST":
        rating = request.POST.get("rating")
        comment = request.POST.get("comment")
        email = request.POST.get("email")
        
        # Cerca o crea il cliente
        customer, created = Customer.objects.get_or_create(
            email=email,
            defaults={"first_name": "Anonymous", "last_name": "User"}
        )
        
        # Crea la recensione
        Review.objects.create(
            car=car,
            customer=customer,
            rating=rating,
            comment=comment
        )
        
        return redirect('car_detail', car_id=car_id)
    
    return render(request, 'rental/add_review.html', {'car': car})

def car_availability(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    unavailable_dates = car.get_unavailable_dates()
    
    return JsonResponse({
        'unavailable_dates': unavailable_dates
    })

def car_detail(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    reviews = Review.objects.filter(car=car).order_by('-created_at')
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    return render(request, 'rental/car_detail.html', {
        'car': car,
        'reviews': reviews,
        'average_rating': round(average_rating, 1),
        'today': date.today().strftime('%Y-%m-%d')
    })

def dashboard(request):
    try:
        # Statistiche auto
        available_cars_count = Car.objects.filter(status='available').count()
        
        # Statistiche noleggi
        active_rentals_count = Rental.objects.filter(
            status__in=['confirmed', 'in_progress']
        ).count()
        
        # Statistiche manutenzioni
        maintenance_count = Maintenance.objects.filter(completed=False).count()
        
        # Calcolo fatturato mensile
        start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_revenue = Payment.objects.filter(
            payment_date__gte=start_of_month,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Noleggi recenti
        recent_rentals = Rental.objects.select_related('car', 'customer').order_by('-start_date')[:5]
        
        # Manutenzioni in corso
        active_maintenance = Maintenance.objects.select_related('car').filter(
            completed=False
        ).order_by('service_date')[:5]
        
        context = {
            'available_cars_count': available_cars_count,
            'active_rentals_count': active_rentals_count,
            'maintenance_count': maintenance_count,
            'monthly_revenue': monthly_revenue,
            'recent_rentals': recent_rentals,
            'active_maintenance': active_maintenance,
        }
        
        return render(request, 'rental/dashboard.html', context)
    except Exception as e:
        # In caso di errore, mostra una dashboard vuota
        context = {
            'available_cars_count': 0,
            'active_rentals_count': 0,
            'maintenance_count': 0,
            'monthly_revenue': 0,
            'recent_rentals': [],
            'active_maintenance': [],
        }
        return render(request, 'rental/dashboard.html', context)

def manage_cars(request):
    cars = Car.objects.all().order_by('-id')
    
    # Statistiche
    total_cars = cars.count()
    available_cars = cars.filter(status='available').count()
    rented_cars = cars.filter(status='rented').count()
    maintenance_cars = cars.filter(status='maintenance').count()
    
    context = {
        'cars': cars,
        'total_cars': total_cars,
        'available_cars': available_cars,
        'rented_cars': rented_cars,
        'maintenance_cars': maintenance_cars,
    }
    
    return render(request, 'rental/manage_cars.html', context)
