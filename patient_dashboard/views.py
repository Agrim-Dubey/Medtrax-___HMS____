from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import PatientDashboardSerializer, DashboardAppointmentSerializer,PatientCompleteProfileSerializer
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

class PatientRecentAppointmentsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
      
            patient = request.user.patient_profile
   
            appointments = patient.appointments.filter(
                appointment_date__lt=date.today(),
                status='completed'
            ).order_by('-appointment_date', '-appointment_time')[:4]
            
     
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
        

class PatientCompleteProfileView(APIView):
        permission_classes = [IsAuthenticated]
            
        def get(self, request):
                try:
                    patient = request.user.patient_profile
                    serializer = PatientCompleteProfileSerializer(patient)
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
        def patch(self, request):
            try:
                patient = request.user.patient_profile

                # Added first_name and last_name to editable fields
                editable_fields = [
                    'first_name', 'last_name',
                    'phone_number', 'emergency_contact', 'emergency_email',
                    'city', 'is_insurance', 'ins_company_name', 'ins_policy_number',
                    'known_allergies', 'chronic_diseases', 'previous_surgeries',
                    'family_medical_history'
                ]
                filtered_data = {
                    key: value for key, value in request.data.items() 
                    if key in editable_fields
                }
                serializer = PatientCompleteProfileSerializer(
                    patient, 
                    data=filtered_data, 
                    partial=True
                )
                
                if serializer.is_valid():
                    serializer.save()
                    return Response(
                        {
                            "message": "Profile updated successfully",
                            "data": serializer.data
                        },
                        status=status.HTTP_200_OK
                    )
                
                return Response(
                    {"error": "Invalid data", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
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

class PatientDashboardStatsView(APIView):
        permission_classes = [IsAuthenticated]
        
        def get(self, request):
            try:
        
                patient = request.user.patient_profile

                total_appointments = patient.appointments.count()
                
                upcoming = patient.appointments.filter(
                    appointment_date__gte=date.today(),
                    status__in=['pending', 'confirmed']
                ).count()
                
                completed = patient.appointments.filter(
                    status='completed'
                ).count()
                
                pending = patient.appointments.filter(
                    status='pending'
                ).count()

                stats = {
                    "total_appointments": total_appointments,
                    "upcoming": upcoming,
                    "completed": completed,
                    "pending": pending
                }

                return Response(stats, status=status.HTTP_200_OK)
                
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

        