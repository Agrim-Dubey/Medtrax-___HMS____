from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
from .models import Medicine, Cart, CartItem, Order, OrderItem
from .serializers import (
    MedicineSerializer, CartSerializer, CartItemSerializer,
    OrderSerializer, CreateOrderSerializer
)


class MedicineListView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get list of all available medicines",
        operation_summary="List Medicines",
        tags=['Pharmacy'],
        manual_parameters=[
            openapi.Parameter('category', openapi.IN_QUERY, description="Filter by category", type=openapi.TYPE_STRING),
            openapi.Parameter('search', openapi.IN_QUERY, description="Search by name", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response(
                description="Medicines retrieved successfully",
                schema=MedicineSerializer(many=True)
            ),
            401: "Unauthorized"
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        try:
            medicines = Medicine.objects.filter(quantity_available__gt=0)
            category = request.query_params.get('category')
            if category:
                medicines = medicines.filter(category=category)
            search = request.query_params.get('search')
            if search:
                medicines = medicines.filter(name__icontains=search)
            
            serializer = MedicineSerializer(medicines, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MedicineDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get medicine details by ID",
        operation_summary="Medicine Details",
        tags=['Pharmacy'],
        responses={
            200: MedicineSerializer,
            404: "Medicine not found",
            401: "Unauthorized"
        },
        security=[{'Bearer': []}]
    )
    def get(self, request, medicine_id):
        try:
            medicine = get_object_or_404(Medicine, id=medicine_id)
            serializer = MedicineSerializer(medicine)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CartView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get current user's cart",
        operation_summary="View Cart",
        tags=['Pharmacy - Cart'],
        responses={
            200: CartSerializer,
            401: "Unauthorized"
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        try:
            cart, created = Cart.objects.get_or_create(user=request.user)
            serializer = CartSerializer(cart)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AddToCartView(APIView):

    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Add medicine to cart",
        operation_summary="Add to Cart",
        tags=['Pharmacy - Cart'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['medicine_id', 'quantity'],
            properties={
                'medicine_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, minimum=1),
            }
        ),
        responses={
            200: "Added to cart successfully",
            400: "Invalid data",
            401: "Unauthorized"
        },
        security=[{'Bearer': []}]
    )
    def post(self, request):
        try:
            medicine_id = request.data.get('medicine_id')
            quantity = request.data.get('quantity', 1)
            
            medicine = get_object_or_404(Medicine, id=medicine_id)
            
            if medicine.quantity_available < quantity:
                return Response(
                    {"error": f"Only {medicine.quantity_available} units available"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            cart, created = Cart.objects.get_or_create(user=request.user)
            
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                medicine=medicine,
                defaults={'quantity': quantity}
            )
            
            if not created:
                new_quantity = cart_item.quantity + quantity
                if medicine.quantity_available < new_quantity:
                    return Response(
                        {"error": f"Cannot add more. Only {medicine.quantity_available} units available"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                cart_item.quantity = new_quantity
                cart_item.save()
            
            return Response(
                {"message": "Added to cart successfully"},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpdateCartItemView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Update cart item quantity",
        operation_summary="Update Cart Item",
        tags=['Pharmacy - Cart'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['quantity'],
            properties={
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, minimum=1),
            }
        ),
        responses={
            200: "Cart updated successfully",
            400: "Invalid quantity",
            401: "Unauthorized"
        },
        security=[{'Bearer': []}]
    )
    def patch(self, request, item_id):
        try:
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            quantity = request.data.get('quantity')
            
            if quantity < 1:
                return Response(
                    {"error": "Quantity must be at least 1"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if cart_item.medicine.quantity_available < quantity:
                return Response(
                    {"error": f"Only {cart_item.medicine.quantity_available} units available"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            cart_item.quantity = quantity
            cart_item.save()
            
            return Response(
                {"message": "Cart updated successfully"},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RemoveFromCartView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Remove item from cart",
        operation_summary="Remove from Cart",
        tags=['Pharmacy - Cart'],
        responses={
            200: "Item removed successfully",
            404: "Item not found",
            401: "Unauthorized"
        },
        security=[{'Bearer': []}]
    )
    def delete(self, request, item_id):
        try:
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            cart_item.delete()
            
            return Response(
                {"message": "Item removed from cart"},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClearCartView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Clear all items from cart",
        operation_summary="Clear Cart",
        tags=['Pharmacy - Cart'],
        responses={
            200: "Cart cleared successfully",
            401: "Unauthorized"
        },
        security=[{'Bearer': []}]
    )
    def delete(self, request):
        try:
            cart = get_object_or_404(Cart, user=request.user)
            cart.items.all().delete()
            
            return Response(
                {"message": "Cart cleared successfully"},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CreateOrderView(APIView):

    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Create order from cart items",
        operation_summary="Create Order",
        tags=['Pharmacy - Orders'],
        request_body=CreateOrderSerializer,
        responses={
            201: openapi.Response(
                description="Order created successfully",
                schema=OrderSerializer
            ),
            400: "Invalid data or empty cart",
            401: "Unauthorized"
        },
        security=[{'Bearer': []}]
    )
    def post(self, request):
        try:
            serializer = CreateOrderSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            cart = get_object_or_404(Cart, user=request.user)
            
            if not cart.items.exists():
                return Response(
                    {"error": "Cart is empty"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user_type = 'doctor' if hasattr(request.user, 'doctor_profile') else 'patient'
            
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    user_type=user_type,
                    total_amount=cart.total_amount,
                    delivery_address=serializer.validated_data['delivery_address'],
                    phone_number=serializer.validated_data['phone_number'],
                    status='pending'
                )
                for cart_item in cart.items.all():
                    medicine = cart_item.medicine
                    if medicine.quantity_available < cart_item.quantity:
                        raise Exception(f"{medicine.name} is out of stock")

                    OrderItem.objects.create(
                        order=order,
                        medicine=medicine,
                        quantity=cart_item.quantity,
                        price_at_purchase=medicine.price
                    )
                    medicine.quantity_available -= cart_item.quantity
                    medicine.save()
                cart.items.all().delete()
                
                order_serializer = OrderSerializer(order)
                return Response(
                    {
                        "message": "Order created successfully",
                        "order": order_serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )
            
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OrderListView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get list of user's orders",
        operation_summary="List Orders",
        tags=['Pharmacy - Orders'],
        responses={
            200: openapi.Response(
                description="Orders retrieved successfully",
                schema=OrderSerializer(many=True)
            ),
            401: "Unauthorized"
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        try:
            orders = Order.objects.filter(user=request.user)
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get order details by ID",
        operation_summary="Order Details",
        tags=['Pharmacy - Orders'],
        responses={
            200: OrderSerializer,
            404: "Order not found",
            401: "Unauthorized"
        },
        security=[{'Bearer': []}]
    )
    def get(self, request, order_id):
        try:
            order = get_object_or_404(Order, order_id=order_id, user=request.user)
            serializer = OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class AdminMedicineUpdateView(APIView):
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Update medicine stock and price (Admin only)",
        operation_summary="Update Medicine Stock",
        tags=['Pharmacy - Admin'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'quantity_available': openapi.Schema(type=openapi.TYPE_INTEGER, minimum=0),
                'price': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
            }
        ),
        responses={
            200: "Medicine updated successfully",
            400: "Invalid data",
            403: "Admin access required"
        },
        security=[{'Bearer': []}]
    )
    def patch(self, request, medicine_id):
        try:
            medicine = get_object_or_404(Medicine, id=medicine_id)
            
            quantity = request.data.get('quantity_available')
            price = request.data.get('price')
            
            if quantity is not None:
                if quantity < 0:
                    return Response(
                        {"error": "Quantity cannot be negative"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                medicine.quantity_available = quantity
            
            if price is not None:
                if price < 0:
                    return Response(
                        {"error": "Price cannot be negative"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                medicine.price = price
            
            medicine.save()
            
            serializer = MedicineSerializer(medicine)
            return Response(
                {
                    "message": "Medicine updated successfully",
                    "medicine": serializer.data
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )