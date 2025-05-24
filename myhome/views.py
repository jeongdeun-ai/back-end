from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from table.models import *
from serializers import *

from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.db import IntegrityError
from django.db import transaction

# Open AI API 사용하기 위한 header
import os
from dotenv import load_dotenv
import openai

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from datetime import datetime
from django.http import HttpResponse
import base64






from table.models import *
from serializers import UserWithParentSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_settings(request):
    user = request.user

    try:
        relation = UserParentRelation.objects.select_related('parent').get(user=user)
    except UserParentRelation.DoesNotExist:
        return Response({'error': 'User is not connected to any Parent.'}, status=status.HTTP_404_NOT_FOUND)

    data = {
        'user': user,
        'parent': relation.parent,
        'relation_type': relation.relation_type,
        'ai_name_called': relation.ai_name_called,
    }

    serializer = UserWithParentSerializer(data)
    return Response(serializer.data, status=status.HTTP_200_OK)
