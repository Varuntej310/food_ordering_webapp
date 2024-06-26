from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomAuthenticationForm, CustomUserCreationForm
from django.shortcuts import render, redirect



from django.contrib.auth import login

class SignupView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

# ... your other view imports

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')  # Or your desired redirect URL
    else:
        form = CustomAuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

    