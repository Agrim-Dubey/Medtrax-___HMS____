from django.db import models
from django.core.validators import MinValueValidator
from Authapi.models import Doctor, Patient, CustomUser

class Medicine(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    manufacturer = models.CharField(max_length=200)
    category = models.CharField(max_length=100, choices=[
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('syrup', 'Syrup'),
        ('injection', 'Injection'),
        ('ointment', 'Ointment'),
        ('drops', 'Drops'),
        ('inhaler', 'Inhaler'),
        ('other', 'Other'),
    ])
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    quantity_available = models.IntegerField(validators=[MinValueValidator(0)])
    dosage = models.CharField(max_length=100)
    expiry_date = models.DateField()
    requires_prescription = models.BooleanField(default=True)
    image_url = models.URLField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.dosage}"
    
    @property
    def is_available(self):
        return self.quantity_available > 0
    
    @property
    def is_low_stock(self):
        return self.quantity_available < 10


class Order(models.Model):
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('payment_initiated', 'Payment Initiated'),
        ('paid', 'Paid'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    USER_TYPE = [
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
    ]
    
    order_id = models.CharField(max_length=100, unique=True, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='pharmacy_orders')
    user_type = models.CharField(max_length=10, choices=USER_TYPE)
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    payment_id = models.CharField(max_length=200, blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    delivery_address = models.TextField()
    phone_number = models.CharField(max_length=15)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_id']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"Order {self.order_id} - {self.user.email}"
    
    def save(self, *args, **kwargs):
        if not self.order_id:
            import uuid
            self.order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['order', 'medicine']),
        ]
    
    def __str__(self):
        return f"{self.medicine.name} x {self.quantity}"
    
    @property
    def subtotal(self):
        return self.quantity * self.price_at_purchase


class Cart(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='pharmacy_cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cart - {self.user.email}"
    
    @property
    def total_amount(self):
        return sum(item.subtotal for item in self.items.all())
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['cart', 'medicine']
    
    def __str__(self):
        return f"{self.medicine.name} x {self.quantity}"
    
    @property
    def subtotal(self):
        return self.quantity * self.medicine.price