from django.shortcuts import render

# Create your views here.
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from home.models import Menu, Category
from orders.models import Orders, OrderItem, Address
from django.contrib.auth.models import User
from cart.models import Cart, CartItem
from .serializers import (
    UserSerializer, MenuSerializer, CategorySerializer, 
    OrderSerializer, AddressSerializer, CartSerializer, CartItemSerializer
)
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework.authtoken.models import Token  # For token-based authentication
from rest_framework.authentication import TokenAuthentication
from .serializers import UserSerializer, LoginSerializer, SignupSerializer
from django.contrib.auth import login, logout
from django.core.mail import send_mail
from django.conf import settings 
from django.utils.crypto import get_random_string
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

from datetime import datetime, timedelta
from django.db.models import Count

User = get_user_model()

# Home API views

class MenuList(generics.ListAPIView):
    authentication_classes = [] 
    permission_classes = [permissions.AllowAny]
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer


class CategoryList(generics.ListAPIView):
    authentication_classes = [] 
    permission_classes = [permissions.AllowAny]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class MenuSearch(generics.ListAPIView):
    authentication_classes = [] 
    permission_classes = [permissions.AllowAny]
    serializer_class = MenuSerializer

    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        if query:
            return Menu.objects.filter(
                Q(item__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query) |
                Q(veg_nonveg_egg__icontains=query) 
            ).distinct()
        else:
            return Menu.objects.all()


# Orders API views

class UserOrderList(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Orders.objects.filter(user=self.request.user)


class Checkout(generics.CreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)

        if not cart_items.exists():
            return Response({"detail": "Your cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = serializer.save(user=request.user)

        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                menu_item=cart_item.menu_item,
                quantity=cart_item.quantity
            )

        cart_items.delete()  # Clear the cart after creating the order

        order_data = self.get_serializer(order).data
        return Response(order_data, status=status.HTTP_201_CREATED)


class AddressList(generics.ListAPIView):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


class CreateAddress(generics.CreateAPIView):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# User API View

class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]  


# cart API Views

class CartView(generics.RetrieveUpdateAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def perform_update(self, serializer):
        cart = serializer.save()
        cart.cart_items.all().delete()  # Clear existing items

        for item_data in self.request.data.get('cart_items', []):
            menu_item = get_object_or_404(Menu, id=item_data['menu_item_id'])
            CartItem.objects.create(
                cart=cart,
                menu_item=menu_item,
                quantity=item_data['quantity']
            )


class CartItemCreate(generics.CreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart_item = serializer.save()
        return Response(CartItemSerializer(cart_item).data, status=status.HTTP_201_CREATED)


class CartItemIncrementDecrement(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        cart_item_id = kwargs.get('pk')
        action = request.data.get('action')

        cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)

        if action == 'increment':
            cart_item.quantity += 1
            cart_item.save()
        elif action == 'decrement':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(CartItemSerializer(cart_item).data, status=status.HTTP_200_OK)


class CartItemDelete(generics.DestroyAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(cart__user=self.request.user)


# authentication API views

class SignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignupSerializer
    authentication_classes = [] 
    permission_classes = [permissions.AllowAny]


from django.contrib.auth.hashers import check_password

class LoginView(generics.GenericAPIView):
    authentication_classes = [] 
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = User.objects.get(phone_number=serializer.validated_data['phone_number'])
        except User.DoesNotExist:
            return Response({'error': 'Wrong Credentials'}, status=status.HTTP_400_BAD_REQUEST)

        if check_password(serializer.validated_data['password'], user.password):
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "user": UserSerializer(user, context=self.get_serializer_context()).data,
                "token": token.key
            })
        else:
            return Response({'error': 'Wrong Credentials'}, status=status.HTTP_400_BAD_REQUEST)


        

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = (TokenAuthentication,) 

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
 
# profile

class GetProfileView(generics.RetrieveAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    

# bestsellers

class BestsellerListView(generics.ListAPIView):
    serializer_class = MenuSerializer
    permission_classes = [permissions.AllowAny]  # Allow access to everyone (no authentication needed)

    def get_queryset(self):
        one_week_ago = datetime.now() - timedelta(days=7)
        bestseller_ids = (
            Orders.objects
            .filter(date__gte=one_week_ago)  # Filter orders from the last week
            .values('items')  # Get unique menu item IDs (through the ManyToMany relationship)
            .annotate(item_count=Count('items'))  # Count occurrences of each menu item
            .order_by('-item_count')  # Order by count (highest first)
            .values_list('items', flat=True)[:5]  # Get top 5 IDs
        )
        return Menu.objects.filter(id__in=bestseller_ids)