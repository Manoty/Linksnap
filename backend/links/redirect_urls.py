# links/redirect_urls.py
# Separated so the redirect route stays clean.
# GET /r/{short_code}/ is the only public-facing URL that matters for traffic.

from django.urls import path
from links.views import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(), name='link-redirect'),
]