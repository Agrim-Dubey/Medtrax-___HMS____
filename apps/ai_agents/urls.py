from django.urls import path
from .care_plan_agent.views import CarePlanView
from .safety_agent.views import ClinicalSafetyCheckView
from .summarizer_agent.views import ClinicalSummarizerView
from .triage_agent.views import SymptomTriageView

urlpatterns = [
    path('safety-check/', ClinicalSafetyCheckView.as_view(), name='ai-clinical-safety-check'),
    path('triage/', SymptomTriageView.as_view(), name='ai-symptom-triage'),
    path('summarize/', ClinicalSummarizerView.as_view(), name='ai-clinical-summarize'),
    path('care-plan/', CarePlanView.as_view(), name='ai-care-plan'),
]

