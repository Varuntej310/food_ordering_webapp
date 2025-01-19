from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        
        # if 'phone_number' in extra_fields:
        #     extra_fields['email'] = self.normalize_email(extra_fields['email'])
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self.db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(email, password, **extra_fields)

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

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return f'{self.email}'
