from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Category, MenuItem, Cart, Order, OrderItem
import bleach
from django.contrib.auth import get_user_model 
from django.db.models import Q
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
   
    def validate(self, attrs): 
        if attrs.get('title', None):
            attrs['title'] = bleach.clean(attrs['title']) 
        if attrs.get('price', None):
            if(attrs['price']<0):
                raise serializers.ValidationError('Price cannot be nagative') 
         
        return super().validate(attrs)
    
    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category', 'category_id']
    def update(self, instance, validated_data):
        featured = validated_data.get('featured')
        instance.title = validated_data.get('title', instance.title)
        instance.price = validated_data.get('price', instance.price)
        instance.category_id = validated_data.get('category_id', instance.category_id)
        if featured == 1 and instance.featured == 0:
            instance.featured = featured
            MenuItem.objects.exclude(id=instance.id).update(featured=0) 

        
        instance.save()

        return instance 
class CartSerializer(serializers.ModelSerializer):
    unit_price = serializers.ReadOnlyField(source='menuitem.price')
    price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'menuitem', 'quantity', 'unit_price', 'price']

    def get_price(self, obj):
        return obj.menuitem.price * obj.quantity

    def create(self, validated_data):
        user = self.context['request'].user
        menuitem = validated_data['menuitem']
        quantity = validated_data['quantity']
        unit_price = menuitem.price
        price = unit_price * quantity

        cart = Cart.objects.create(user=user, menuitem=menuitem, quantity=quantity, unit_price=unit_price, price=price)
        return cart
class OrderItemSerializer(serializers.ModelSerializer):
    menuitem = MenuItemSerializer()

    class Meta: 
        model = OrderItem
        fields = ['id', 'menuitem', 'quantity', 'unit_price', 'price']


class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, read_only=True) 
    status = serializers.BooleanField()

    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew', 'status', 'total', 'date', 'order_items']
        read_only_fields = ['user']
    def get_delivery_crew(self, obj):
        delivery_crew = obj.delivery_crew
        if delivery_crew:
            serializer = UserSerializer(delivery_crew)
            return serializer.data
        return None
    def validate_delivery_crew(self, value):
        user = self.context['request'].user

        if not user.groups.filter(name='Manager').exists() and value is not None:
            raise serializers.ValidationError('You do not have permission to assign a delivery crew.')

        return value

    def validate_status(self, value):
        user = self.context['request'].user
        instance = getattr(self, 'instance', None)
        manager_role , delivery_crew_role , customer_role = False, False, False
        if user.groups.filter(name='Manager').exists():
            manager_role  = True
        elif user.groups.filter(name='Delivery crew').exists():
            delivery_crew_role = True
        else:
            customer_role = True
        if not manager_role and not delivery_crew_role:
            raise serializers.ValidationError('You do not have permission to update the status.')
        
        if delivery_crew_role:
            # Check if the user is the same as the order's delivery_crew 
            if instance.delivery_crew == user:
                #if  value != True:
                #    raise serializers.ValidationError('You do not have permission to update the status to 0')
                #else:
                return value
            else:
                raise serializers.ValidationError('You do not have permission to update the status. You are not the same delivery crew assigned to this order!')
        # Check if the user is in Manager role
        if not manager_role and instance is not None and instance.status != False:
            raise serializers.ValidationError('You do not have permission to update the status.')

        return value

    def update(self, instance, validated_data):
        delivery_crew = validated_data.get('delivery_crew', instance.delivery_crew)
        status = validated_data.get('status', instance.status)
        user = self.context['request'].user

        # Check if the delivery_crew value is an instance of User model
        if isinstance(delivery_crew, User):
            instance.delivery_crew = delivery_crew
        else:
            # Convert the delivery_crew ID to User instance
            try:
                instance.delivery_crew = User.objects.get(pk=delivery_crew)
            except User.DoesNotExist:
                instance.delivery_crew = None

        instance.status = status
        instance.save()

        return instance 