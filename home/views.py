from django.shortcuts import render
from django.views import View
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, redirect

from .models import Menu, Category
from cart.models import Cart, CartItem


# Create your views here.
class Index(View):
    def get(self, request, *args, **kwargs):
        menu_items = Menu.objects.all()
        print(menu_items)
        
        # Check for authentication
        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            cart_items = CartItem.objects.filter(cart=cart)
        else:
            cart_items = []  # Empty list if not authenticated
        
        context = {
            'menu_items': menu_items,
            'cart_items': cart_items,
        }
        return render(request, 'home/index.html', context)
    

@login_required
def remove_from_cart_from_home(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)

    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()

    return redirect('home')


def search_menu(request):
    query = request.GET.get('q')
    if query:
        menu_items = Menu.objects.filter(
            Q(item__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(veg_or_nonveg__icontains=query)
        ).distinct()
    else:
        menu_items = Menu.objects.all()
        query = ''

    context = {
        'menu_items': menu_items,
        'query': query,
    }
    return render(request, 'home/search.html', context)


@login_required
def add_to_cart_from_search(request, item_id):
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

    return redirect('search_menu')