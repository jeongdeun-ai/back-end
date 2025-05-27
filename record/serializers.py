from rest_framework import serializers
from table.models import *


class DailyReportSerializers(serializers.ModelSerializer):
    class Meta:
        model = DailyReport
        fileds = "__all__"

