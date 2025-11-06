from rest_framework import serializers
from .models import Medicine, Order, OrderItem, Cart, CartItem
from django.utils import timezone

class MedicineSerializer(serializers.ModelSerializer):
    is_available = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = Medicine
        fields = [
            'id', 'name', 'description', 'manufacturer', 'category',
            'price', 'quantity_available', 'dosage', 'expiry_date',
            'requires_prescription', 'image_url', 'is_available',
            'is_low_stock', 'is_expired', 'created_at', 'updated_at'
        ]
    
    def get_is_expired(self, obj):
        return obj.expiry_date < timezone.now().date()


class CartItemSerializer(serializers.ModelSerializer):
    medicine = MedicineSerializer(read_only=True)
    medicine_id = serializers.IntegerField(write_only=True)
    subtotal = serializers.ReadOnlyField()
    
    class Meta:
        model = CartItem
        fields = ['id', 'medicine', 'medicine_id', 'quantity', 'subtotal', 'created_at']
    
    def validate(self, data):
        medicine_id = data.get('medicine_id')
        quantity = data.get('quantity', 1)
        
        try:
            medicine = Medicine.objects.get(id=medicine_id)
        except Medicine.DoesNotExist:
            raise serializers.ValidationError("Medicine not found")
        
        if medicine.quantity_available < quantity:
            raise serializers.ValidationError(
                f"Only {medicine.quantity_available} units available"
            )
        
        if medicine.expiry_date < timezone.now().date():
            raise serializers.ValidationError("This medicine has expired")
        
        return data


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.ReadOnlyField()
    total_items = serializers.ReadOnlyField()
    
    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_amount', 'total_items', 'created_at', 'updated_at']


class OrderItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    medicine_dosage = serializers.CharField(source='medicine.dosage', read_only=True)
    subtotal = serializers.ReadOnlyField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'medicine', 'medicine_name', 'medicine_dosage', 
                  'quantity', 'price_at_purchase', 'subtotal']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_id', 'user', 'user_email', 'user_type',
            'total_amount', 'status', 'payment_id', 'payment_method',
            'delivery_address', 'phone_number', 'items',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['order_id', 'user', 'user_type']


class CreateOrderSerializer(serializers.Serializer):
    delivery_address = serializers.CharField()
    phone_number = serializers.CharField(max_length=15)
    
    def validate_phone_number(self, value):
        if not value.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise serializers.ValidationError("Invalid phone number format")
        return value