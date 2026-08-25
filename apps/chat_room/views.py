from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import ChatRoom, Message, DoctorConnection
from .serializers import (
    ChatRoomListSerializer, ChatRoomDetailSerializer,
    MessageSerializer, DoctorConnectionSerializer,
    DoctorConnectionListSerializer, DoctorMinimalSerializer
)
from authentication.models import Doctor
from .throttles import (
    ChatListThrottle, ChatMessageThrottle,
    ChatConnectionThrottle, ChatSearchThrottle,
    ChatReadThrottle
)
from .selectors import (
    get_user_chat_rooms,
    get_pending_doctor_connections,
    search_doctors_for_chat,
    get_chat_room_detail
)
from .services import (
    accept_doctor_connection,
    reject_doctor_connection,
    send_chat_message,
    mark_chat_messages_as_read
)


class PatientChatViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ChatListThrottle]

    @swagger_auto_schema(
        operation_summary="List patient's doctor chats",
        tags=["Chat"]
    )
    def list(self, request):
        if request.user.role != "patient":
            return Response({"error": "Only patients allowed"}, status=403)

        chat_rooms = get_user_chat_rooms(user=request.user, room_type="patient_doctor")
        
        serializer = ChatRoomListSerializer(chat_rooms, many=True, context={"request": request})
        return Response(serializer.data)


class DoctorChatViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ChatListThrottle]

    @swagger_auto_schema(
        operation_summary="List doctor's patient chats",
        tags=["Chat"]
    )
    def list_patients(self, request):
        if request.user.role != "doctor":
            return Response({"error": "Only doctors allowed"}, status=403)

        chat_rooms = get_user_chat_rooms(user=request.user, room_type="patient_doctor")

        serializer = ChatRoomListSerializer(chat_rooms, many=True, context={"request": request})
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="List doctor's doctor-to-doctor chats",
        tags=["Chat"]
    )
    def list_doctors(self, request):
        if request.user.role != "doctor":
            return Response({"error": "Only doctors allowed"}, status=403)

        chat_rooms = get_user_chat_rooms(user=request.user, room_type="doctor_doctor")

        serializer = ChatRoomListSerializer(chat_rooms, many=True, context={"request": request})
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Send a doctor-to-doctor connection request",
        request_body=DoctorConnectionSerializer,
        tags=["Chat"]
    )
    @action(detail=False, methods=["post"], throttle_classes=[ChatConnectionThrottle])
    def send_connection_request(self, request):
        if request.user.role != "doctor":
            return Response({"error": "Only doctors allowed"}, status=403)

        serializer = DoctorConnectionSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)

    @swagger_auto_schema(
        operation_summary="List pending doctor connection requests",
        tags=["Chat"]
    )
    def list_pending_requests(self, request):
        if request.user.role != "doctor":
            return Response({"error": "Only doctors allowed"}, status=403)

        qs = get_pending_doctor_connections(doctor=request.user.doctor_profile)

        serializer = DoctorConnectionListSerializer(qs, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Accept a doctor connection request",
        tags=["Chat"]
    )
    def accept_connection(self, request, pk):
        if request.user.role != "doctor":
            return Response({"error": "Only doctors allowed"}, status=403)

        connection = accept_doctor_connection(connection_id=pk, to_doctor=request.user.doctor_profile)

        return Response(DoctorConnectionSerializer(connection).data)

    @swagger_auto_schema(
        operation_summary="Reject a doctor connection request",
        tags=["Chat"]
    )
    def reject_connection(self, request, pk):
        if request.user.role != "doctor":
            return Response({"error": "Only doctors allowed"}, status=403)

        reject_doctor_connection(connection_id=pk, to_doctor=request.user.doctor_profile)

        return Response({"message": "Connection rejected"})

    @swagger_auto_schema(
        operation_summary="Search doctors",
        manual_parameters=[
            openapi.Parameter("q", openapi.IN_QUERY, type=openapi.TYPE_STRING, description="Search keyword")
        ],
        tags=["Chat"]
    )
    @action(detail=False, methods=["get"], throttle_classes=[ChatSearchThrottle])
    def search_doctors(self, request):
        if request.user.role != "doctor":
            return Response({"error": "Only doctors allowed"}, status=403)

        q = request.query_params.get("q", "").strip()
        if not q:
            return Response({"error": "Query param 'q' is required"}, status=400)

        doctors = search_doctors_for_chat(query=q, current_user=request.user)

        return Response(DoctorMinimalSerializer(doctors, many=True).data)


class ChatRoomViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Chat"])
    def retrieve(self, request, pk):
        from django.core.exceptions import PermissionDenied
        try:
            chat_room = get_chat_room_detail(room_id=pk, user=request.user)
            if not chat_room:
                return Response(
                    {"error": "Chat room not found", "detail": "This chat may have been deleted"},
                    status=404
                )
            serializer = ChatRoomDetailSerializer(chat_room, context={"request": request})
            return Response(serializer.data)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=403)

    @swagger_auto_schema(tags=["Chat"])
    @action(detail=True, methods=["post"], throttle_classes=[ChatMessageThrottle])
    def send_message(self, request, pk):
        from django.core.exceptions import PermissionDenied
        content = request.data.get("content", "").strip()
        if not content:
            return Response({"error": "Message content required"}, status=400)

        try:
            message = send_chat_message(room_id=pk, sender=request.user, content=content)
            return Response(MessageSerializer(message).data, status=201)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=403)

    @swagger_auto_schema(tags=["Chat"])
    @action(detail=True, methods=["post"], throttle_classes=[ChatReadThrottle])
    def mark_as_read(self, request, pk):
        from django.core.exceptions import PermissionDenied
        try:
            mark_chat_messages_as_read(room_id=pk, user=request.user)
            return Response({"message": "Messages marked as read"})
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=403)