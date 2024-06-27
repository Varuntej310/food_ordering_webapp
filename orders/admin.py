from django.contrib import admin
from .models import Orders, Address, OrderItem

# Register your models here.
admin.site.register(Orders)
admin.site.register(Address)
admin.site.register(OrderItem)