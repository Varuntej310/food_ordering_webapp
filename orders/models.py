from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from home.models import Menu
from datetime import datetime
import pytz

from django.dispatch import receiver
from django.db.models.signals import post_save
from asgiref.sync import async_to_sync
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

    PICKUP_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('ready', 'Ready for Pickup'),
        ('completed', 'Completed'),
    ]

    DELIVERY_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
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
        default='pending'
    )
    address = models.TextField(
        null=True,
        blank=True
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    def get_status_choices(self):
        if self.mode_of_eating == 'delivery':
            return self.DELIVERY_STATUS_CHOICES
        return self.PICKUP_STATUS_CHOICES

    def clean(self):
        from django.core.exceptions import ValidationError
        valid_statuses = [status for status, _ in self.get_status_choices()]
        if self.status not in valid_statuses:
            raise ValidationError({'status': 'Invalid status for this mode of eating'})

    def save(self, *args, **kwargs):
        if self.status in ['completed', 'delivered'] and not self.completed_at:
            self.completed_at = timezone.now()
        self.clean()
        super().save(*args, **kwargs)
        self.notify_status_change()

    def notify_status_change(self):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"order_{self.id}",
            {
                "type": "order.status.update",
                "order_id": self.id,
                "status": self.status,
                "timestamp": timezone.now().isoformat(),
            }
        )

    def get_total_price(self):
        return sum(item.get_cost() for item in self.items.all())

    def _str_(self):
        return f'{self.user} | {self.date.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y %H:%M:%S")}'

    def get_next_status(self):
        current_status = self.status
        choices = self.get_status_choices()
        current_index = next(i for i, (status, _) in enumerate(choices) if status == current_status)

        if current_index < len(choices) - 1:
            return choices[current_index + 1][0]
        return current_status

    def get_next_status_display(self):
        next_status = self.get_next_status()
        return dict(self.get_status_choices())[next_status]


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

    def _str_(self):
        return str(self.phone_number)


# @receiver(post_save, sender=Orders)
# def order_status_changed(sender, instance, created, **kwargs):
#     if not created:
#         instance.notify_status_change()