from django.db import models
from django.contrib.auth.models import User
from datetime import date, timedelta

#garage delle auto disponibili
class Car(models.Model):
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year =  models.IntegerField()   
    horsepower = models.IntegerField()
    color = models.CharField(max_length=30) 
    description = models.TextField(blank=True, null=True)
    deposit = models.DecimalField(max_digits=10, decimal_places=2) #deposito pre noleggio
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="car_images/", null=True, blank=True)
    minimum_age = models.IntegerField(null=True, blank=True)
    available_locations = models.ForeignKey('Location', on_delete=models.SET_NULL, null=True, blank=True)
    

    def __str__(self):
        return f"{self.brand} {self.model} - {self.color} - {self.horsepower}CV - Deposit: {self.deposit}€ - {self.price_per_day}€/day"

    def is_available(self, start_date, end_date):
        overlapping_rentals = self.rental_set.filter(
            end_date__gte=start_date,
            start_date__lte=end_date
        ).exists()
        return not overlapping_rentals

    def get_unavailable_dates(self):
        unavailable_dates = []
        rentals = self.rental_set.all()
        for rental in rentals:
            delta = rental.end_date - rental.start_date
            for i in range(delta.days + 1):
                unavailable_dates.append(
                    (rental.start_date + timedelta(days=i)).strftime('%Y-%m-%d')
                )
        return unavailable_dates

#clienti
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=100, default="nome")
    last_name = models.CharField(max_length=100, default="cognome")
    email = models.EmailField(default= "ex@mail.com")

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
#assicurazioni 
class Insurance(models.Model):
    name = models.CharField(max_length=100)  # Basic, Premium, Full Coverage
    description = models.TextField()
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    coverage_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} Insurance - {self.price_per_day}€/day"
    
#noleggi
class Rental(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    insurance = models.ForeignKey(Insurance, on_delete=models.SET_NULL, null=True, blank=True)  
    start_date = models.DateField()
    end_date = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pickup_location = models.ForeignKey('Location', on_delete=models.SET_NULL, null=True, related_name='pickups')

    def calculate_total_price(self):
        rental_days = (self.end_date - self.start_date).days
        base_price = self.car.price_per_day * rental_days
        insurance_price = self.insurance.price_per_day * rental_days if self.insurance else 0
        self.total_price = base_price + insurance_price
        return self.total_price

    def __str__(self):
        return f"Rental: {self.car.brand} {self.car.model} from {self.start_date} to {self.end_date} - {self.customer}"

#pagamenti
class Payment(models.Model):
    rental = models.OneToOneField("Rental", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method= models.CharField(max_length=50)
    payment_date= models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices = [("pending", "Pending"), ('completed', 'Completed')], default='pending')

    def __str__(self):
        return f"Payment for {self.rental} - {self.amount}€ "
    
#recensioni
class Review(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stelle
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review for {self.car.brand} {self.car.model} by {self.customer} - {self.rating} stars"

    class Meta:
        unique_together = ('car', 'customer')  # Ogni cliente può recensire un'auto solo una volta

#Sede ritiro auto
class Location(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    city = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    opening_hours = models.CharField(max_length=200)  

    def __str__(self):
        return f"{self.name} - {self.city}"

#manutenzioni
class Maintenance(models.Model):
    MAINTENANCE_TYPES = [
        ('routine', 'Routine Check'),
        ('repair', 'Repair'),
        ('inspection', 'Inspection'),
        ('tire_change', 'Tire Change'),
        ('oil_change', 'Oil Change')
    ]

    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='maintenances')
    service_date = models.DateField()
    service_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES)
    description = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.car} - {self.get_service_type_display()} on {self.service_date}"