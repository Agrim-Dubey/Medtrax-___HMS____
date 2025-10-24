from django.shortcuts import render

# Create your views here.

def chat_home(request):
    return render(request, "chat_room/chat.html")
