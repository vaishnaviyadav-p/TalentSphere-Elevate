from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from .models import UserProfile
from .forms import RegisterForm
from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    return redirect("login")
    
def home(request):
    return render(request, "accounts/home.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if user.is_superuser:
                return redirect("/recruiter/dashboard/")

            try:
                profile = UserProfile.objects.get(user=user)

                if profile.role == "candidate":
                    return redirect("candidate_profile")

                elif profile.role == "recruiter":
                    return redirect("recruiter_profile")

            except UserProfile.DoesNotExist:
                return redirect("/")

        return render(request, "accounts/login.html", {
            "error": "Invalid username or password"
        })

    return render(request, "accounts/login.html")

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            role = form.cleaned_data["role"]

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            UserProfile.objects.create(
                user=user,
                role=role
            )

            print("Registration Successful")
            return redirect("/login/")
        else:
            print(form.errors)

    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})
