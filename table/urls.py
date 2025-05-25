from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *


router = DefaultRouter()
router.register(r'user', UserViewSet)
router.register(r'parent', ParentViewSet)
router.register(r'user_parent_relation', UserParentRelationViewSet)
router.register(r'chatLog', ChatLogViewSet)
router.register(r'daily_report', DailyReportViewSet)
router.register(r'context_summary', ContextSummaryViewSet)
router.register(r'event', EventViewSet)
router.register(r'medication_schedule', MedicationScheduleViewSet)
router.register(r'medication_item', MedicationItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
]