from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from cart.models import Cart, CartItem
from home.models import Menu, Category
from orders.models import Orders, OrderItem, PhoneNumber

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
    item_price = serializers.DecimalField(source='menu_item.price', max_digits=10, decimal_places=2, read_only=True)
    item_image = serializers.ImageField(source='menu_item.image', read_only=True)
    category = serializers.SlugRelatedField(source='menu_item.category', many=True, slug_field='name', read_only=True)
    veg_nonveg_egg = serializers.CharField(source='menu_item.veg_nonveg_egg', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'menu_item', 'item_name', 'quantity', 'item_price', 'item_image', 'category', 'veg_nonveg_egg']
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


# cart

class CartItemSerializer(serializers.ModelSerializer):
    # menu_item_id = serializers.IntegerField()  # Keep this for input
    menu_item = MenuSerializer(read_only=True)  # For output

    class Meta:
        model = CartItem
        fields = ['id', 'quantity', 'menu_item']
        read_only_fields = ['id']
         
        
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
        fields = ['id', 'email', 'name', 'hostel']

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
    

class BulkCartItemSerializer(serializers.Serializer):
    menu_item_id = serializers.IntegerField()
    quantity = serializers.IntegerField()

    def validate_menu_item_id(self, value):
        if not Menu.objects.filter(id=value).exists():
            raise serializers.ValidationError("Menu item does not exist.")
        return value

    def create(self, validated_data):
        cart = self.context['cart']
        menu_item = Menu.objects.get(id=validated_data['menu_item_id'])
        return CartItem.objects.create(cart=cart, menu_item=menu_item, quantity=validated_data['quantity'])


class PhoneNumberUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneNumber
        fields = ['phone_number']

    def validate_phone_number(self, value):
        # Check if phone number already exists for another user
        if PhoneNumber.objects.exclude(user=self.context['request'].user).filter(phone_number=value).exists():
            raise serializers.ValidationError("This phone number is already in use.")
        return value