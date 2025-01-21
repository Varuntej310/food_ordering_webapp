from django.contrib import admin
from .models import Orders, OrderItem, PhoneNumber

# Register your models here.
admin.site.register(Orders)
admin.site.register(OrderItem)
admin.site.register(PhoneNumber)