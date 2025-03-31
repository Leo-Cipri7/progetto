from django.shortcuts import render, redirect, get_object_or_404
from .models import Car, Customer, Rental, Payment, Review
from django.db.models import Avg
from datetime import datetime, date
from django.db import models

from django.contrib import messages

from django.contrib.auth.models import User  

from django.db.models.signals import post_save
from django.dispatch import receiver


def car_list(request):
    # Ottieni i parametri di filtro dalla query string
    brand = request.GET.get('brand')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    min_hp = request.GET.get('min_hp')
    
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
    
    # Aggiungi la valutazione media per ogni auto
    for car in cars:
        car.average_rating = Review.objects.filter(car=car).aggregate(Avg('rating'))['rating__avg']
    
    # Ottieni tutte le marche disponibili per il filtro
    brands = Car.objects.values_list('brand', flat=True).distinct()
    
    context = {
        'cars': cars,
        'brands': brands,
        'selected_brand': brand,
        'min_price': min_price,
        'max_price': max_price,
        'min_hp': min_hp,
    }
    
    return render(request, "rental/car_list.html", context)


def rent_car(request, car_id):
    car = get_object_or_404(Car, id=car_id)

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

        # Calcola il prezzo totale
        rental_days = (end_date - start_date).days
        total_price = rental_days * car.price_per_day

        # Crea il noleggio
        rental = Rental.objects.create(
            car=car,
            customer=customer,
            start_date=start_date,
            end_date=end_date,
            total_price=total_price
        )

        rental.save()

        # Crea un record di pagamento in stato "pending"
        payment = Payment.objects.create(
            rental=rental,
            amount=total_price,
            payment_method="Credit Card",  # Default value
            status="pending"
        )
        
        # Redirect alla pagina di pagamento
        return redirect('process_payment', payment_id=payment.id)


    return render(request, 'rental/rent_car.html', {'car': car})


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

def car_detail(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    reviews = Review.objects.filter(car=car).order_by('-created_at')
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    return render(request, 'rental/car_detail.html', {
        'car': car,
        'reviews': reviews,
        'average_rating': round(average_rating, 1)
    })
