from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from home.models import Menu
from datetime import datetime
import pytz

from django.db.models.signals import post_save
from asgiref.sync import async_to_sync
from django.dispatch import receiver
from channels.layers import get_channel_layer

User = get_user_model()

def get_current_datetime():
    return datetime.now(pytz.timezone('Asia/Kolkata'))

def get_current_time():
    return datetime.now(pytz.timezone('Asia/Kolkata')).time()

class Orders(models.Model):
    EAT_MODES = [
        ('take-away', 'Take-away'),
        ('dine-in', 'Dine-in'),
        ('delivery', 'Delivery'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('ready', 'Ready'),
        ('confirmed', 'Confirmed'),
        ('delivered', 'Delivered'),
        ('canceled', 'Canceled'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='orders'
    )
    mode_of_eating = models.CharField(
        max_length=100, 
        choices=EAT_MODES
    )
    date = models.DateTimeField(default=get_current_datetime)
    time = models.TimeField(default=get_current_time)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    address = models.TextField(
        null=True, 
        blank=True
    )

    def get_total_price(self):
        return sum(item.get_cost() for item in self.items.all())
    
    def __str__(self):
        return f'{self.user} | {self.date.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y %H:%M:%S")}'

class OrderItem(models.Model):
    order = models.ForeignKey(
        Orders, 
        related_name='items', 
        on_delete=models.CASCADE
    )
    menu_item = models.ForeignKey(
        Menu, 
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1)

    def get_cost(self):
        return self.menu_item.price * self.quantity

class PhoneNumber(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='phone_numbers'
    )
    phone_number = PhoneNumberField(
        null=True, 
        blank=True, 
        default=None
    )

    def __str__(self):
        return str(self.phone_number)



@receiver(post_save, sender=Orders)
def send_order_update(sender, instance, **kwargs):
    if not kwargs.get('created'):  # Trigger only on updates, not creation
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{instance.user.id}',
            {
                'type': 'order_update',
                'data': {
                    'order_id': instance.id,
                    'status': instance.status,
                }
            }
        )