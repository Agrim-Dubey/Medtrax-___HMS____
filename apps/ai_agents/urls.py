from django.urls import path
from .safety_agent.views import ClinicalSafetyCheckView
from .summarizer_agent.views import ClinicalSummarizerView
from .triage_agent.views import SymptomTriageView

urlpatterns = [
    path('safety-check/', ClinicalSafetyCheckView.as_view(), name='ai-clinical-safety-check'),
    path('triage/', SymptomTriageView.as_view(), name='ai-symptom-triage'),
    path('summarize/', ClinicalSummarizerView.as_view(), name='ai-clinical-summarize'),
]

