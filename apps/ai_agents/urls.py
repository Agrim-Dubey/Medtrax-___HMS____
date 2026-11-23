from django.urls import path
from .appointment_agent.views import SmartAppointmentAssistantView
from .care_plan_agent.views import CarePlanView
from .safety_agent.views import ClinicalSafetyCheckView
from .summarizer_agent.views import ClinicalSummarizerView
from .triage_agent.views import SymptomTriageView
from .views import AIAgentsRegistryView

urlpatterns = [
    path('agents/', AIAgentsRegistryView.as_view(), name='ai-agents-registry'),
    path('safety-check/', ClinicalSafetyCheckView.as_view(), name='ai-clinical-safety-check'),
    path('triage/', SymptomTriageView.as_view(), name='ai-symptom-triage'),
    path('symptom-triage/', SymptomTriageView.as_view(), name='ai-symptom-triage-alias'),
    path('summarize/', ClinicalSummarizerView.as_view(), name='ai-clinical-summarize'),
    path('care-plan/', CarePlanView.as_view(), name='ai-care-plan'),
    path('appointment-assistant/', SmartAppointmentAssistantView.as_view(), name='ai-appointment-assistant'),
]

