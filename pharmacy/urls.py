from django.urls import path
from .views import (
    MedicineListView,
    MedicineDetailView,
    CartView,
    AddToCartView,
    UpdateCartItemView,
    RemoveFromCartView,
    ClearCartView,
    CreateOrderView,
    OrderListView,
    OrderDetailView,
    AdminMedicineUpdateView,
)

urlpatterns = [
    path('medicines/', MedicineListView.as_view(), name='medicine-list'),
    path('medicines/<int:medicine_id>/', MedicineDetailView.as_view(), name='medicine-detail'),
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/add/', AddToCartView.as_view(), name='add-to-cart'),
    path('cart/item/<int:item_id>/', UpdateCartItemView.as_view(), name='update-cart-item'),
    path('cart/item/<int:item_id>/remove/', RemoveFromCartView.as_view(), name='remove-from-cart'),
    path('cart/clear/', ClearCartView.as_view(), name='clear-cart'),
    path('orders/', OrderListView.as_view(), name='order-list'),
    path('orders/create/', CreateOrderView.as_view(), name='create-order'),
    path('orders/<str:order_id>/', OrderDetailView.as_view(), name='order-detail'),
    path('admin/medicines/<int:medicine_id>/update/', AdminMedicineUpdateView.as_view(), name='admin-update-medicine'),
]