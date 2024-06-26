from django.db import models
from django.contrib.auth.models import User
from home.models import Menu
from django.db.models import Sum

from datetime import date, time
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your models here.
class Orders(models.Model):
    EAT_MODES = [('take-away', 'Take-away'),
                 ('dine-in', 'Dine-in'),
                 ('delivery', 'Delivery'),]
    STATUS_CHOICES = [('pending', 'Pending'),
                    ('ready', 'Ready'),
                    ('confirmed', 'Confirmed'),
                    ('delivered', 'Delivered'),
                    ('canceled', 'Canceled')]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    mode_of_eating = models.CharField(max_length=100, choices=EAT_MODES)
    date = models.DateField(default=timezone.now)
    time = models.TimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    address = models.ForeignKey('Address', on_delete=models.SET_NULL, null=True, blank=True)

    def get_total_price(self):
        return sum(item.get_cost() for item in self.items.all())
    
    def __str__(self):
        return f'{self.user} | {self.date}'

class OrderItem(models.Model):
    order = models.ForeignKey(Orders, related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(Menu, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def get_cost(self):
        return self.menu_item.price * self.quantity
    


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address = models.TextField()

    def __str__(self):
        return f"{self.address}"