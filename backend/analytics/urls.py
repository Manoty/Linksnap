from django.urls import path
from analytics.views import DashboardStatsView, LinkStatsView, RecentActivityView

urlpatterns = [
    path('dashboard/', DashboardStatsView.as_view(), name='analytics-dashboard'),
    path('links/<str:short_code>/', LinkStatsView.as_view(), name='analytics-link'),
    path('activity/', RecentActivityView.as_view(), name='analytics-activity'),
]