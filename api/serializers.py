from rest_framework import serializers
from django.contrib.auth.models import User
from home.models import Menu, Category
from orders.models import Orders, Address
from cart.models import Cart, CartItem
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from phonenumber_field.serializerfields import PhoneNumberField
from django.contrib.auth.hashers import make_password

User = get_user_model()

# Home 

class MenuSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(many=True, slug_field='name', read_only=True)
    class Meta:
        model = Menu
        fields = ['id', 'item', 'description', 'price', 'category', 'veg_nonveg_egg', 'image', 'avg_time_taken', 'is_available']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'image']


# Orders 

class OrderSerializer(serializers.ModelSerializer):
    items = serializers.SlugRelatedField(many=True, slug_field='item', read_only=True)
    get_total_price = serializers.SerializerMethodField()

    def get_get_total_price(self, obj):
        return obj.get_total_price()

    class Meta:
        model = Orders
        fields = ['id', 'items', 'mode_of_eating', 'date', 'time', 'status', 'address', 'get_total_price']


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'address']


# cart

class CartItemSerializer(serializers.ModelSerializer):
    menu_item = MenuSerializer(read_only=True)  

    class Meta:
        model = CartItem
        fields = ['id', 'menu_item', 'quantity']
         
        
class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True, source='cart_items')  

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items']
        read_only_fields = ['user']


# authentication

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'name', 'hostel', 'email']

class LoginSerializer(serializers.Serializer):
    phone_number = PhoneNumberField()
    password = serializers.CharField(required=True)


class SignupSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    class Meta:
        model = User
        fields = ['phone_number', 'email', 'password', 'password2', 'name', 'hostel']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        del validated_data['password2']
        return User.objects.create_user(**validated_data)