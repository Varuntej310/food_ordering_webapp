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
    menu_item_id = serializers.IntegerField()

    class Meta:
        model = CartItem
        fields = ['menu_item_id', 'quantity']

    def create(self, validated_data):
        user = self.context['request'].user
        cart, _ = Cart.objects.get_or_create(user=user)
        menu_item_id = validated_data.pop('menu_item_id')
        menu_item = Menu.objects.get(id=menu_item_id)
        quantity = validated_data.get('quantity', 1)
        
        cart_items = CartItem.objects.filter(cart=cart, menu_item=menu_item)
        
        if cart_items.exists():
            cart_item = cart_items.first()
            cart_item.quantity = F('quantity') + quantity
            cart_item.save()
            # Refresh from db to get the updated quantity
            cart_item.refresh_from_db()
        else:
            cart_item = CartItem.objects.create(
                cart=cart,
                menu_item=menu_item,
                quantity=quantity
            )

        return cart_item
         
        
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
        del validated_data['password2']
        return User.objects.create_user(**validated_data)