from django.shortcuts import render

def test_video_doctor(request, room_id):
    return render(request, "videocounselling/doctor_call.html", {"room_id": room_id})

def test_video_patient(request, room_id):
    return render(request, "videocounselling/patient_call.html", {"room_id": room_id})

