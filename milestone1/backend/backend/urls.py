from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static
from accounts.views import home


urlpatterns = [
    path("admin/", admin.site.urls),

    # Accounts
    path("", include("accounts.urls")),

    # Candidate
    path(
        "candidate/",
        include("candidate.urls")
    ),


    # Recruiter
    path(
        "recruiter/",
        include("recruiter.urls")
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        
        settings.MEDIA_URL,
       
        document_root=settings.MEDIA_ROOT
    ,
    )