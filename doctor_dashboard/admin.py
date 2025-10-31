from django.contrib import admin
from .models import DoctorReview, PatientVisit

@admin.register(DoctorReview)
class DoctorReviewAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'patient', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']

@admin.register(PatientVisit)
class PatientVisitAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'patient', 'visit_date']
    list_filter = ['visit_date']