from rest_framework import serializers
from table.models import User, Parent, UserParentRelation

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'phone_number']

        read_only_fileds = ['id', 'email'] # id, email 변동 불가

class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = ['id', 'name', 'birth_date', 'sex', 'address', 'disease_info', 'medication_info']

        read_only_fileds = ['id'] # id 값은 변동 불가




class UserWithParentSerializer(serializers.Serializer):
    user = UserSerializer()
    parent = ParentSerializer()
    relation_type = serializers.CharField()
    ai_name_called = serializers.CharField()


