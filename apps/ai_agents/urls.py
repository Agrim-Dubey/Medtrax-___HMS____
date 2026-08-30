from django.urls import path
from .safety_agent.views import ClinicalSafetyCheckView

urlpatterns = [
    path('safety-check/', ClinicalSafetyCheckView.as_view(), name='ai-clinical-safety-check'),
]

