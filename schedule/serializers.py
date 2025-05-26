from rest_framework import serializers
from table.models import *

class GetEventsForSpecificDateSerializers(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'


