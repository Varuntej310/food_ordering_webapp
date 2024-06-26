from rest_framework import serializers
from django.contrib.auth.models import User
from home.models import Menu, Category
from orders.models import Orders, OrderItem, Address
from cart.models import Cart, CartItem
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from phonenumber_field.serializerfields import PhoneNumberField
from django.contrib.auth.hashers import make_password
from django.db.models import F
from django.shortcuts import get_object_or_404

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

class OrderItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='menu_item.item', read_only=True)
    price = serializers.DecimalField(source='menu_item.price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'menu_item', 'item_name', 'quantity', 'price']
        read_only_fields = ['id']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Orders
        fields = ['id', 'items', 'mode_of_eating', 'date', 'time', 'status', 'address', 'total_price']
        read_only_fields = ['status', 'time']

    def get_total_price(self, obj):
        return obj.get_total_price()


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'address']


# cart

class CartItemSerializer(serializers.ModelSerializer):
    menu_item_id = serializers.IntegerField()  # Keep this for input
    menu_item = MenuSerializer(read_only=True)  # For output

    class Meta:
        model = CartItem
        fields = ['menu_item_id', 'quantity', 'menu_item']
         
        
class CartSerializer(serializers.ModelSerializer):
    cart_items = CartItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Cart
        fields = ['id', 'user', 'cart_items']
        read_only_fields = ['user']

    def update(self, instance, validated_data):
        cart_items_data = self.context['request'].data.get('cart_items', [])
        instance.cart_items.all().delete()
        
        for item_data in cart_items_data:
            menu_item = get_object_or_404(Menu, id=item_data['menu_item_id'])
            CartItem.objects.create(
                cart=instance,
                menu_item=menu_item,
                quantity=item_data['quantity']
            )
        
        return instance


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
        del validated_data['password2']
        return User.objects.create_user(**validated_data)