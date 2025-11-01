from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import PatientDashboardSerializer, DashboardAppointmentSerializer
from django.utils import timezone
from datetime import datetime, date

class PatientDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try :
            patient = request.user.patient_profile
            serializer = PatientDashboardSerializer(patient)
            return Response(serializer.data ,status=status.HTTP_200_OK)
        except AttributeError :
            return Response(
                {"error": "Only patients can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
# patient_dashboard/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from datetime import date
from .serializers import PatientDashboardSerializer, DashboardAppointmentSerializer


class PatientDashboardProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            patient = request.user.patient_profile
            serializer = PatientDashboardSerializer(patient)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except AttributeError:
            return Response(
                {"error": "Only patients can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PatientUpcomingAppointmentsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
 
            patient = request.user.patient_profile
     
            appointments = patient.appointments.filter(
                appointment_date__gte=date.today(),
                status__in=['pending', 'confirmed']
            ).order_by('appointment_date', 'appointment_time')[:4] 
   
            serializer = DashboardAppointmentSerializer(appointments, many=True)
    
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except AttributeError:
            return Response(
                {"error": "Only patients can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



        