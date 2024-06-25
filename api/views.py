from django.shortcuts import render

# Create your views here.
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from home.models import Menu, Category
from orders.models import Orders, Address
from django.contrib.auth.models import User
from cart.models import Cart, CartItem
from .serializers import (
    UserSerializer, MenuSerializer, CategorySerializer, 
    OrderSerializer, AddressSerializer, CartSerializer, CartItemSerializer
)
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework.authtoken.models import Token  # For token-based authentication
from .serializers import UserSerializer, LoginSerializer, SignupSerializer
from django.contrib.auth import login, logout
from django.core.mail import send_mail
from django.conf import settings 
from django.utils.crypto import get_random_string
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

User = get_user_model()

# Home API views

class MenuList(generics.ListAPIView):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer


class CategoryList(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class MenuSearch(generics.ListAPIView):
    serializer_class = MenuSerializer

    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        if query:
            return Menu.objects.filter(
                Q(item__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query) |
                Q(veg_or_nonveg__icontains=query)
            ).distinct()
        else:
            return Menu.objects.all()


# Orders API views

class UserOrderList(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Orders.objects.filter(user=self.request.user)


class CreateOrder(generics.CreateAPIView):
    queryset = Orders.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]


class AddressList(generics.ListAPIView):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


class CreateAddress(generics.CreateAPIView):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]


# User API View

class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]  


# cart API Views

class CartView(generics.ListAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)  


class CartItemCreateUpdate(generics.CreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        menu_item = serializer.validated_data['menu_item']
        
        cart_item, created = CartItem.objects.get_or_create(cart=cart, menu_item=menu_item)
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        else:
            serializer.save(cart=cart)

        return cart_item

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart_item = self.perform_create(serializer)
        return Response(self.get_serializer(cart_item).data, status=status.HTTP_200_OK if not cart_item else status.HTTP_201_CREATED)
    


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


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(**serializer.validated_data)

        if user:
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key})
        else:
            return Response({'error': 'Wrong Credentials'}, status=status.HTTP_400_BAD_REQUEST)
        

class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)