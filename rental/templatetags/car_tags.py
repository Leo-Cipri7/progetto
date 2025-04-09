from django import template
from django.db.models import Sum

register = template.Library()

@register.filter
def sum_payments(rentals):
    return rentals.aggregate(total=Sum('payment__amount'))['total'] or 0 