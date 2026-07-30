from django.shortcuts import render

def home(request):
    return render(request, 'accounts/home.html')

def login_view(request):
    return render(request, 'accounts/login.html')

def register_view(request):
    return render(request, 'accounts/register.html')