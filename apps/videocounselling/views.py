from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from appointments.models import Appointment
from .models import VideoCall
from .serializers import VideoCallSerializer
from .selectors import get_video_call_by_appointment
from .services import initiate_video_call, join_video_call, end_video_call
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError


class InitiateVideoCall(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, appointment_id):
        try:
            video_call = initiate_video_call(appointment_id=appointment_id, user=request.user)
            serializer = VideoCallSerializer(video_call)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except DjangoValidationError as e:
            return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # For 404s from get_object_or_404
            if "not found" in str(e).lower():
                 return Response({'error': 'Appointment not found'}, status=status.HTTP_404_NOT_FOUND)
            raise e


class JoinVideoCall(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, appointment_id):
        try:
            video_call = join_video_call(appointment_id=appointment_id, user=request.user)
            serializer = VideoCallSerializer(video_call)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except DjangoValidationError as e:
            return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            if "not found" in str(e).lower():
                 return Response({'error': 'Appointment or Call not found'}, status=status.HTTP_404_NOT_FOUND)
            raise e


class EndVideoCall(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, appointment_id):
        try:
            video_call = end_video_call(appointment_id=appointment_id, user=request.user)
            serializer = VideoCallSerializer(video_call)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except DjangoValidationError as e:
            return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            if "not found" in str(e).lower():
                 return Response({'error': 'Appointment or Call not found'}, status=status.HTTP_404_NOT_FOUND)
            raise e


class VideoCallStatus(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, appointment_id):
        try:
            video_call = get_video_call_by_appointment(appointment_id=appointment_id, user=request.user)
            if not video_call:
                return Response({'error': 'No call found'}, status=status.HTTP_404_NOT_FOUND)
            serializer = VideoCallSerializer(video_call)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            if "not found" in str(e).lower():
                 return Response({'error': 'Appointment not found'}, status=status.HTTP_404_NOT_FOUND)
            raise e