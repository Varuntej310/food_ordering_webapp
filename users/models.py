from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.

class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('Phone number is required')
        
        extra_fields['email'] = self.normalize_email(extra_fields['email'])
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self.db)

        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(phone_number, password, **extra_fields)

class CustomUser(AbstractUser):
    HOSTELS = [('kameng', 'Kameng'),
                 ('lohit', 'Lohit'),
                 ('barak', 'Barak'),
                 ('umiam', 'Umiam'),
                 ('siang', 'Siang'),
                 ('subansiri', 'Subansiri'),
                 ('dhansiri', 'Dhansiri'),
                 ('kapili', 'Kapili'),
                 ('disang', 'Disang'),
                 ('gaurang', 'Gaurang')]
    username = None
    email = models.EmailField(unique=True)
    phone_number = PhoneNumberField(unique=True)
    name = models.CharField(max_length=100)
    hostel = models.CharField(max_length=20, choices=HOSTELS)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return f'{self.name}'
