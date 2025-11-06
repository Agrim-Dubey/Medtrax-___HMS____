from django.contrib import admin
from .models import Medicine, Order, OrderItem, Cart, CartItem


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ['name', 'dosage', 'category', 'price', 'quantity_available', 'is_available', 'expiry_date']
    list_filter = ['category', 'requires_prescription', 'expiry_date']
    search_fields = ['name', 'manufacturer']
    list_editable = ['price', 'quantity_available']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'manufacturer', 'category')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'quantity_available', 'dosage')
        }),
        ('Additional Details', {
            'fields': ('expiry_date', 'requires_prescription', 'image_url')
        }),
    )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['medicine', 'quantity', 'price_at_purchase', 'subtotal']
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user', 'user_type', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'user_type', 'created_at']
    search_fields = ['order_id', 'user__email']
    readonly_fields = ['order_id', 'user', 'user_type', 'total_amount', 'created_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'user', 'user_type', 'total_amount', 'status')
        }),
        ('Payment Details', {
            'fields': ('payment_id', 'payment_method')
        }),
        ('Delivery Information', {
            'fields': ('delivery_address', 'phone_number')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_items', 'total_amount', 'updated_at']
    search_fields = ['user__email']
    readonly_fields = ['user', 'total_items', 'total_amount']


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'medicine', 'quantity', 'subtotal']
    search_fields = ['cart__user__email', 'medicine__name']
    readonly_fields = ['subtotal']