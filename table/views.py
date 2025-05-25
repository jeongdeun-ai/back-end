from rest_framework.viewsets import ModelViewSet
from .models import *
from .serializers import *

MedicationItem

class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class ParentViewSet(ModelViewSet):
    queryset = Parent.objects.all()
    serializer_class = ParentSerializer

class UserParentRelationViewSet(ModelViewSet):
    queryset = UserParentRelation.objects.all()
    serializer_class = UserParentRelationSerializer

class ChatLogViewSet(ModelViewSet):
    queryset = ChatLog.objects.all()
    serializer_class = ChatLogSerializer

class DailyReportViewSet(ModelViewSet):
    queryset = DailyReport.objects.all()
    serializer_class = DailyReportSerializer

class ContextSummaryViewSet(ModelViewSet):
    queryset = ContextSummary.objects.all()
    serializer_class = ContextSummarySerializer

class EventViewSet(ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

class MedicationScheduleViewSet(ModelViewSet):
    queryset = MedicationSchedule.objects.all()
    serializer_class = MedicationScheduleSerializer

class MedicationItemViewSet(ModelViewSet):
    queryset = MedicationItem.objects.all()
    serializer_class = MedicationItemSerializer
