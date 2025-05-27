from rest_framework import serializers
from table.models import *


class DailyReportSerializers(serializers.ModelSerializer):
    class Meta:
        model = DailyReport
        fields = "__all__"


class ChatLogSerializers(serializers.ModelSerializer):
    class Meta:
        model = ChatLog
        fields = "__all__"