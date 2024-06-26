from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from phonenumber_field.modelfields import PhoneNumberField

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('phone_number', 'email', 'name', 'hostel') 

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Phone Number")

    def clean_username(self):
        phone_number = self.cleaned_data.get('username')
        if phone_number and not User.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError("Invalid phone number or password.")
        return phone_number
