from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

from django.http import HttpResponse
from django_ratelimit.exceptions import Ratelimited


# ============================================================
# CUSTOM 403 HANDLER
# ============================================================

def custom_403(request, exception=None):

    # Rate limit exceeded
    if isinstance(exception, Ratelimited):

        return HttpResponse(
            "Too Many Requests - Rate limit exceeded.",
            status=429
        )

    # Other forbidden requests
    return HttpResponse(
        "Forbidden",
        status=403
    )


# ============================================================
# URL PATTERNS
# ============================================================

urlpatterns = [

    # Admin
    path(
        "admin/",
        admin.site.urls
    ),

# Accounts
    path(
        "",
        include("accounts.urls")
    ),

    path(
        "candidate/",
        include("candidate.urls")
    ),

# Recruiter
    path(
        "recruiter/",
        include("recruiter.urls")
    ),

    path(
        "recommendations/",
        include("recommendations.urls")
    ),
]


# ============================================================
# CUSTOM ERROR HANDLER
# ============================================================

handler403 = custom_403


# ============================================================
# MEDIA FILES - DEVELOPMENT
# ============================================================

if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
