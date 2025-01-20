# Create your views here.
from datetime import timedelta
import os

from django.contrib.auth import get_user_model
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token  # For token-based authentication
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.models import Cart, CartItem
from home.models import Menu, Category
from orders.models import Orders, OrderItem, Address
from .serializers import (
    MenuSerializer, CategorySerializer,
    OrderSerializer, AddressSerializer, CartSerializer, CartItemSerializer, BulkCartItemSerializer
)
from .serializers import UserSerializer, LoginSerializer, SignupSerializer
from rest_framework_simplejwt.tokens import AccessToken

from google.oauth2 import id_token
from google.auth.transport import requests

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
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item = serializer.save(cart=cart)
        return Response(CartItemSerializer(cart_item).data, status=status.HTTP_201_CREATED)


class CartItemIncrementDecrement(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        cart_item_id = kwargs.get('pk')
        action = request.data.get('action')

        cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)

        if action == 'increment':
            cart_item.quantity += 1
        elif action == 'decrement':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
            else:
                cart_item.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            
        cart_item.save()
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
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        one_week_ago = timezone.now() - timedelta(days=7)
        bestseller_ids = (
            OrderItem.objects
            .filter(order__date__gte=one_week_ago)
            .values('menu_item')
            .annotate(total_quantity=Sum('quantity'))
            .order_by('total_quantity')
            .values_list('menu_item', flat=True)[:5]
        )
        return Menu.objects.filter(id__in=bestseller_ids)
    

class BulkAddToCartView(generics.GenericAPIView):
    serializer_class = BulkCartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(data=request.data, many=True, context={'cart': cart})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Items added to cart successfully."}, status=status.HTTP_201_CREATED)
    

class LoginWithGoogle(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            if 'credential' not in request.data:
                return Response({'error': 'No credential provided'}, 
                              status=status.HTTP_400_BAD_REQUEST)

            # Your Google OAuth2 client ID
            CLIENT_ID = os.environ.get('client_id')
            
            # Verify the token
            id_info = id_token.verify_oauth2_token(
                request.data['credential'], 
                requests.Request(), 
                CLIENT_ID
            )

            # Get user email from verified token
            email = id_info['email']
            
            # Check if email is verified by Google
            if not id_info.get('email_verified'):
                return Response({'error': 'Email not verified by Google'}, 
                              status=status.HTTP_400_BAD_REQUEST)

            # Get or create user
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = User.objects.create_user(
                    email=email,
                    name=id_info.get('name', ''),
                    # Set a random password since they're using Google login
                    password=User.objects.make_random_password()
                )

            # Generate token
            token = AccessToken.for_user(user)
            
            return Response({
                'token': str(token),
                'email': email,
                'name': user.name
            })

        except ValueError:
            # Invalid token
            return Response({'error': 'Invalid client_id'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, 
                          status=status.HTTP_400_BAD_REQUEST)