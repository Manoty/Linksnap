# links/urls.py
# Link endpoint routing.

from django.urls import path
from links.views import (
    AnonymousLinkCreateView,
    LinkDetailView,
    LinkListCreateView,
    RedirectView,
)

urlpatterns = [
    # Anonymous shortening (no auth required)
    path('shorten/', AnonymousLinkCreateView.as_view(), name='link-shorten'),

    # Authenticated link management
    path('', LinkListCreateView.as_view(), name='link-list-create'),
    path('<str:short_code>/', LinkDetailView.as_view(), name='link-detail'),
    path('r/<str:short_code>/', RedirectView.as_view(), name='link-redirect'),
]