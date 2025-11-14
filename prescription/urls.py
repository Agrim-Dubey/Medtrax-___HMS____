from django.urls import path 

url_patterns = [
    path("/prescription-doctor",doctor_prescription_view.as_view(),name="docpres"),
    path("/prescription-patient",patient_prescription_view.as_view(),name="patpres"),
    path("/give-prescription",send_prescription_view.as_view(),name="give-prescription"),
]