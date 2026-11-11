"""
Clinical Note & Prescription Summarizer AI Agent.
Supports structured doctor SOAP note generation and plain-language patient summaries
with abnormal vital-sign flagging and optional LLM polishing.
"""
from datetime import date
from typing import Any, Dict, List, Optional

from ai_agents.core import (
    HybridLLMClient,
    build_agent_metadata,
    calculate_age,
    is_non_clinical_placeholder,
    sanitize_clinical_text,
)
from appointments.models import Appointment
from prescription.models import Prescription

_FREQUENCY_READABLE = {
    "once_daily": "once a day",
    "twice_daily": "twice a day (morning and night)",
    "thrice_daily": "three times a day",
    "four_times_daily": "four times a day",
    "as_needed": "only as needed",
    "before_meals": "before meals",
    "after_meals": "after meals",
    "at_bedtime": "at bedtime",
}

_SOAP_SYSTEM_PROMPT = (
    "You are a clinical documentation assistant. Given de-identified consultation data, "
    "return JSON with keys: 'executive_summary' (2 concise clinical sentences) and "
    "'clinical_pearls' (array of up to 2 short clinical follow-up reminders)."
)

_PATIENT_SYSTEM_PROMPT = (
    "You are a patient health literacy assistant. Translate the de-identified prescription "
    "into warm, plain 6th-grade reading level English. Return JSON with keys: "
    "'plain_summary' (2 clear sentences) and 'key_takeaways' (array of up to 3 short tips)."
)


class ClinicalSummarizerAgent:
    """Generates SOAP notes for doctors and plain-language prescription guides for patients."""

    def __init__(self, model_name: str = "clinical-summarizer-v1.0", llm_client: Optional[HybridLLMClient] = None):
        self.model_name = model_name
        self.llm_client = llm_client or HybridLLMClient()

    def summarize(
        self,
        *,
        mode: str = "clinical_soap",
        prescription: Optional[Prescription] = None,
        appointment: Optional[Appointment] = None,
        chief_complaint: str = "",
        clinical_notes: str = "",
        diagnosis: str = "",
        vitals: Optional[Dict[str, Any]] = None,
        medications: Optional[List[Dict[str, Any]]] = None,
        lab_tests: Optional[List[Dict[str, Any]]] = None,
        follow_up_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        vitals = dict(vitals or {})
        meds_list = list(medications or [])
        labs_list = list(lab_tests or [])
        patient = None

        if prescription is not None:
            patient = prescription.patient
            chief_complaint = chief_complaint or prescription.chief_complaint or ""
            diagnosis = diagnosis or prescription.diagnosis or ""
            clinical_notes = clinical_notes or prescription.additional_notes or ""
            follow_up_date = follow_up_date or prescription.follow_up_date
            if prescription.blood_pressure and "blood_pressure" not in vitals:
                vitals["blood_pressure"] = prescription.blood_pressure
            if prescription.temperature is not None and "temperature_f" not in vitals:
                vitals["temperature_f"] = float(prescription.temperature)
            if prescription.pulse_rate is not None and "heart_rate" not in vitals:
                vitals["heart_rate"] = prescription.pulse_rate
            if prescription.weight is not None and "weight_kg" not in vitals:
                vitals["weight_kg"] = float(prescription.weight)

            if not meds_list:
                meds_list = [
                    {
                        "medicine_name": m.medicine_name,
                        "dosage": m.dosage,
                        "frequency": m.frequency,
                        "duration": m.duration,
                        "duration_unit": m.duration_unit,
                        "instructions": m.instructions or "",
                    }
                    for m in prescription.medications.all()
                ]
            if not labs_list:
                labs_list = [
                    {"test_name": lt.test_name, "instructions": lt.instructions or ""}
                    for lt in prescription.lab_tests.all()
                ]
        elif appointment is not None:
            patient = appointment.patient
            chief_complaint = chief_complaint or appointment.reason or ""
            clinical_notes = clinical_notes or appointment.notes or ""

        clean_cc = sanitize_clinical_text(chief_complaint, max_length=1500).text
        clean_notes = sanitize_clinical_text(clinical_notes, max_length=2000).text
        clean_diag = sanitize_clinical_text(diagnosis, max_length=1000).text

        abnormal_vitals = self._analyze_vitals(vitals)
        age = calculate_age(getattr(patient, "date_of_birth", None)) if patient else None
        chronic = getattr(patient, "chronic_diseases", None) if patient else None

        if mode == "patient_friendly":
            return self._build_patient_summary(
                diagnosis=clean_diag,
                chief_complaint=clean_cc,
                clinical_notes=clean_notes,
                meds_list=meds_list,
                labs_list=labs_list,
                follow_up_date=follow_up_date,
                abnormal_vitals=abnormal_vitals,
                age=age,
            )

        return self._build_clinical_soap(
            chief_complaint=clean_cc,
            clinical_notes=clean_notes,
            diagnosis=clean_diag,
            vitals=vitals,
            abnormal_vitals=abnormal_vitals,
            meds_list=meds_list,
            labs_list=labs_list,
            follow_up_date=follow_up_date,
            age=age,
            chronic=chronic,
        )

    def _analyze_vitals(self, vitals: Dict[str, Any]) -> List[str]:
        flags: List[str] = []
        bp = vitals.get("blood_pressure")
        if bp and "/" in str(bp):
            try:
                s_str, d_str = str(bp).strip().split("/", 1)
                sys_v, dia_v = int(s_str), int(d_str)
                if sys_v >= 140 or dia_v >= 90:
                    flags.append(f"Elevated BP ({sys_v}/{dia_v} mmHg)")
                elif sys_v < 90 or dia_v < 60:
                    flags.append(f"Low BP ({sys_v}/{dia_v} mmHg)")
            except ValueError:
                pass

        temp = vitals.get("temperature_f")
        if temp is not None:
            try:
                t_val = float(temp)
                if t_val >= 100.4:
                    flags.append(f"Febrile ({t_val}°F)")
                elif t_val < 96.0:
                    flags.append(f"Low temperature ({t_val}°F)")
            except (TypeError, ValueError):
                pass

        hr = vitals.get("heart_rate")
        if hr is not None:
            try:
                hr_val = int(hr)
                if hr_val > 100:
                    flags.append(f"Tachycardia ({hr_val} bpm)")
                elif hr_val < 60:
                    flags.append(f"Bradycardia ({hr_val} bpm)")
            except (TypeError, ValueError):
                pass

        return flags

    def _build_clinical_soap(
        self,
        *,
        chief_complaint: str,
        clinical_notes: str,
        diagnosis: str,
        vitals: Dict[str, Any],
        abnormal_vitals: List[str],
        meds_list: List[Dict[str, Any]],
        labs_list: List[Dict[str, Any]],
        follow_up_date: Optional[date],
        age: Optional[int],
        chronic: Optional[str],
    ) -> Dict[str, Any]:
        subjective_parts = []
        if chief_complaint:
            subjective_parts.append(f"Chief Complaint: {chief_complaint}.")
        if clinical_notes:
            subjective_parts.append(f"Clinical Context: {clinical_notes}.")
        subjective = " ".join(subjective_parts) or "No subjective complaints documented."

        vital_bits = [f"{k}: {v}" for k, v in vitals.items() if v not in (None, "")]
        objective = f"Recorded vitals: {', '.join(vital_bits)}." if vital_bits else "No vitals recorded."
        if abnormal_vitals:
            objective += f" Abnormal findings: {'; '.join(abnormal_vitals)}."

        assessment_parts = []
        if diagnosis:
            assessment_parts.append(f"Primary Diagnosis: {diagnosis}.")
        else:
            assessment_parts.append("Working assessment pending definitive diagnosis.")
        if age is not None:
            assessment_parts.append(f"Patient age: {age}y.")
        if not is_non_clinical_placeholder(chronic):
            assessment_parts.append(f"Relevant comorbidities: {chronic}.")
        assessment = " ".join(assessment_parts)

        plan_items: List[str] = []
        for m in meds_list:
            name = m.get("medicine_name", "Unknown")
            dosage = m.get("dosage", "")
            freq = _FREQUENCY_READABLE.get(m.get("frequency", ""), m.get("frequency", ""))
            dur = f"{m.get('duration', '')} {m.get('duration_unit', '')}".strip()
            plan_items.append(f"Rx: {name} {dosage} ({freq}) for {dur}".strip())
        for lt in labs_list:
            plan_items.append(f"Lab Order: {lt.get('test_name', 'Lab test')}")
        if follow_up_date:
            plan_items.append(f"Follow-up scheduled on {follow_up_date.isoformat()}.")
        plan_text = " ".join(plan_items) if plan_items else "Supportive monitoring and follow-up as needed."

        summary = f"SOAP Summary — S: {subjective} A: {assessment}"
        key_highlights = abnormal_vitals + plan_items[:4]

        llm_result = self.llm_client.generate_json(
            system_prompt=_SOAP_SYSTEM_PROMPT,
            user_payload={
                "age_years": age,
                "chief_complaint": chief_complaint,
                "diagnosis": diagnosis,
                "vitals": vitals,
                "abnormal_vitals": abnormal_vitals,
                "medications": [m.get("medicine_name") for m in meds_list],
                "lab_tests": [lt.get("test_name") for lt in labs_list],
            },
            required_keys=("executive_summary", "clinical_pearls"),
        )
        if llm_result.success and llm_result.data:
            exec_sum = str(llm_result.data.get("executive_summary", "")).strip()
            if exec_sum:
                summary = exec_sum
            pearls = llm_result.data.get("clinical_pearls") or []
            if isinstance(pearls, list):
                key_highlights.extend(str(p).strip() for p in pearls[:2] if isinstance(p, str) and p.strip())

        return {
            "mode": "clinical_soap",
            "summary": summary,
            "soap_note": {
                "subjective": subjective,
                "objective": objective,
                "assessment": assessment,
                "plan": plan_text,
            },
            "abnormal_vitals": abnormal_vitals,
            "medication_guide": meds_list,
            "lab_test_guide": labs_list,
            "key_highlights": key_highlights,
            "agent_metadata": build_agent_metadata(
                agent_name="MedTrax Clinical Summarizer Agent",
                version=self.model_name,
                llm_result=llm_result,
            ),
        }

    def _build_patient_summary(
        self,
        *,
        diagnosis: str,
        chief_complaint: str,
        clinical_notes: str,
        meds_list: List[Dict[str, Any]],
        labs_list: List[Dict[str, Any]],
        follow_up_date: Optional[date],
        abnormal_vitals: List[str],
        age: Optional[int],
    ) -> Dict[str, Any]:
        med_guide = []
        for m in meds_list:
            name = m.get("medicine_name", "Medication")
            dosage = m.get("dosage", "")
            freq_text = _FREQUENCY_READABLE.get(m.get("frequency", ""), m.get("frequency", "as directed"))
            dur = f"{m.get('duration', '')} {m.get('duration_unit', '')}".strip()
            instr = m.get("instructions") or "Take as directed by your doctor."
            med_guide.append({
                "medicine_name": name,
                "plain_instruction": f"Take {name} ({dosage}) {freq_text}" + (f" for {dur}." if dur else "."),
                "notes": instr,
            })

        lab_guide = []
        for lt in labs_list:
            tname = lt.get("test_name", "Lab test")
            prep = lt.get("instructions") or (
                "Fasting for 8-12 hours may be required; confirm with the lab."
                if any(k in tname.lower() for k in ("fasting", "lipid", "glucose", "sugar"))
                else "Follow standard laboratory instructions."
            )
            lab_guide.append({"test_name": tname, "preparation": prep})

        diag_phrase = f"for {diagnosis}" if diagnosis else (f"regarding {chief_complaint}" if chief_complaint else "")
        summary = (
            f"Your visit summary {diag_phrase}: you have {len(med_guide)} prescribed medication(s)"
            + (f" and {len(lab_guide)} recommended lab test(s)." if lab_guide else ".")
        ).strip()
        if follow_up_date:
            summary += f" Please return for your follow-up on {follow_up_date.isoformat()}."

        highlights = [mg["plain_instruction"] for mg in med_guide[:3]]
        if abnormal_vitals:
            highlights.append(f"Vitals noted during visit: {', '.join(abnormal_vitals)}.")
        if clinical_notes:
            highlights.append(f"Doctor's note: {clinical_notes}")

        llm_result = self.llm_client.generate_json(
            system_prompt=_PATIENT_SYSTEM_PROMPT,
            user_payload={
                "age_years": age,
                "diagnosis": diagnosis,
                "medications": [mg["plain_instruction"] for mg in med_guide],
                "lab_tests": [lg["test_name"] for lg in lab_guide],
                "follow_up_date": follow_up_date.isoformat() if follow_up_date else None,
            },
            required_keys=("plain_summary", "key_takeaways"),
        )
        if llm_result.success and llm_result.data:
            plain_sum = str(llm_result.data.get("plain_summary", "")).strip()
            if plain_sum:
                summary = plain_sum
            takeaways = llm_result.data.get("key_takeaways") or []
            if isinstance(takeaways, list):
                highlights.extend(str(t).strip() for t in takeaways[:3] if isinstance(t, str) and t.strip())

        return {
            "mode": "patient_friendly",
            "summary": summary,
            "soap_note": None,
            "abnormal_vitals": abnormal_vitals,
            "medication_guide": med_guide,
            "lab_test_guide": lab_guide,
            "key_highlights": highlights,
            "agent_metadata": build_agent_metadata(
                agent_name="MedTrax Clinical Summarizer Agent",
                version=self.model_name,
                llm_result=llm_result,
            ),
        }
