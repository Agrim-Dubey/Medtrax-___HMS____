"""
Role-based access control and object-level ownership checks for AI clinical agents.
Prevents unauthorized role access and IDOR cross-patient data exposure.
"""
from typing import Optional, Tuple

from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from appointments.models import Appointment
from authentication.models import Doctor, Patient
from prescription.models import Prescription


def get_doctor_profile(user) -> Optional[Doctor]:
    if not user or not user.is_authenticated or not user.is_active:
        return None
    if getattr(user, "role", None) != "doctor":
        return None
    return getattr(user, "doctor_profile", None)


def get_patient_profile(user) -> Optional[Patient]:
    if not user or not user.is_authenticated or not user.is_active:
        return None
    if getattr(user, "role", None) != "patient":
        return None
    return getattr(user, "patient_profile", None)


class IsDoctor(BasePermission):
    """Allows access strictly to active, authenticated users with a Doctor profile."""

    message = "Only authenticated doctors can access this clinical agent."

    def has_permission(self, request, view) -> bool:
        return get_doctor_profile(request.user) is not None


class IsPatient(BasePermission):
    """Allows access strictly to active, authenticated users with a Patient profile."""

    message = "Only authenticated patients can access this clinical agent."

    def has_permission(self, request, view) -> bool:
        return get_patient_profile(request.user) is not None


class IsDoctorOrPatient(BasePermission):
    """Allows access to active authenticated users with either a Doctor or Patient profile."""

    message = "A valid doctor or patient profile is required to access this AI agent."

    def has_permission(self, request, view) -> bool:
        return (
            get_doctor_profile(request.user) is not None
            or get_patient_profile(request.user) is not None
        )


def doctor_has_patient_relationship(doctor: Doctor, patient: Patient) -> bool:
    """
    Verifies an existing clinical relationship between doctor and patient via
    appointments or prescriptions.
    """
    return (
        Appointment.objects.filter(doctor=doctor, patient=patient).exists()
        or Prescription.objects.filter(doctor=doctor, patient=patient).exists()
    )


def resolve_authorized_patient(
    request,
    patient_id: Optional[int],
    *,
    require_doctor_relationship: bool = True,
) -> Tuple[Optional[Patient], Optional[Response]]:
    """
    Resolves the target Patient object while enforcing strict ownership / relationship checks:
    - Patients can only access their own profile (patient_id omitted or matching self).
    - Doctors must provide patient_id and (when required) have a clinical relationship.
    """
    patient_profile = get_patient_profile(request.user)
    doctor_profile = get_doctor_profile(request.user)

    if patient_profile is not None:
        if patient_id is not None and patient_id != patient_profile.id:
            return None, Response(
                {
                    "success": False,
                    "error": "You are not authorized to access another patient's medical data.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        return patient_profile, None

    if doctor_profile is not None:
        if patient_id is None:
            return None, Response(
                {
                    "success": False,
                    "error": "patient_id is required when requesting on behalf of a patient.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            target_patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return None, Response(
                {"success": False, "error": f"Patient with ID {patient_id} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if require_doctor_relationship and not doctor_has_patient_relationship(
            doctor_profile, target_patient
        ):
            return None, Response(
                {
                    "success": False,
                    "error": "You do not have an established clinical relationship with this patient.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        return target_patient, None

    return None, Response(
        {"success": False, "error": "A valid doctor or patient profile is required."},
        status=status.HTTP_403_FORBIDDEN,
    )
