from django.db import models
from django.contrib.auth.models import User

#garage
class Car(models.Model):
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year =  models.IntegerField()   #anno di produzione auto
    horsepower = models.IntegerField()
    color = models.CharField(max_length=30) #colore auto
    description = models.TextField(blank=True, null=True)
    deposit = models.DecimalField(max_digits=10, decimal_places=2) #deposito pre noleggio
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    
    image = models.ImageField(upload_to="car_images/", null=True, blank=True)
    minimum_age = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.brand} {self.model} - {self.color} - {self.horsepower}CV - Deposit: {self.deposit}€ - {self.price_per_day}€/day"


#clienti
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=100, default="nome")
    last_name = models.CharField(max_length=100, default="cognome")
    email = models.EmailField(default= "ex@mail.com")

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
#noleggi
class Rental(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

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
        unique_together = ('car', 'customer')  # Un cliente può recensire un'auto solo una volta