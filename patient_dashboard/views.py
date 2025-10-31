from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import PatientDashboardSerializer 

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


        