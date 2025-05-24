from rest_framework import serializers
from table.models import User, Parent, UserParentRelation

class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = ['id', 'name', 'birth_date', 'sex', 'address', 'disease_info', 'medication_info']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'phone_number']

class UserWithParentSerializer(serializers.Serializer):
    user = UserSerializer()
    parent = ParentSerializer()
    relation_type = serializers.CharField()
    ai_name_called = serializers.CharField()


