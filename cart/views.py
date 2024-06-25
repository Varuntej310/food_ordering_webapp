from django.forms import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django import forms
from home.models import Menu
from .models import Cart, CartItem
from orders.models import Orders, Address
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your views here.
@login_required
def cart_view(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    cart_total = sum(cart_item.menu_item.price * cart_item.quantity for cart_item in cart_items)
    context = {
        'cart_items': cart_items,
        'cart_total': cart_total
    }
    return render(request, 'cart/cart.html', context)



@login_required
def add_to_cart(request, item_id):
    item = get_object_or_404(Menu, id=item_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        menu_item=item,
        defaults={'quantity': 1}
    )

    if not item_created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('home')



@login_required
def remove_from_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)

    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()

    return redirect('cart_view')



class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Orders 
    template_name = 'cart/order_create.html'
    fields = ['mode_of_eating', 'address']

    def get_success_url(self):
        return reverse_lazy('order_placed', kwargs={'pk': self.object.pk})
    
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
    
    def get_form(self ,form_class=None):
        form = super().get_form(form_class)
        if self.request.user.is_authenticated:
            form.fields['address'].queryset = Address.objects.filter(user=self.request.user)
        else:
            form.fields['address'].queryset = Address.objects.none()
        return form
    
    def form_valid(self, form):
        cart = Cart.objects.get(user=self.request.user)
        cart_items = CartItem.objects.filter(cart=cart)

        order = form.save(commit=False)

        order.user = self.request.user
        order.save()

        order.items.set(cart_item.menu_item for cart_item in cart_items)

        cart_items.delete()
        self.object = order

        return redirect(self.get_success_url())
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cart = Cart.objects.get(user=self.request.user)
        cart_items = CartItem.objects.filter(cart=cart)

        context['cart_items'] = cart_items
        context['cart_total'] = sum(cart_item.menu_item.price * cart_item.quantity for cart_item in cart_items)

        return context
        
        

@login_required
def order_placed(request, pk):
    order = get_object_or_404(Orders, pk=pk, user=request.user)
    context = {
        'order': order
    }
    return render(request, 'cart/order_placed.html', context)