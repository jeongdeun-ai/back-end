from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from table.models import *
from .serializers import *

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

# 1번 - User가 '설정' 페이지에 들어갔을 때 본인과 parent의 정보들을 보내는 get 메서드
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def get_user_settings(request):
#     user = request.user

#     try:
#         relation = UserParentRelation.objects.select_related('parent').get(user=user)
#     except UserParentRelation.DoesNotExist:
#         return Response({'error': 'User is not connected to any Parent.'}, status=status.HTTP_404_NOT_FOUND)

#     data = {
#         'user_name': user,
#         'parent': relation.parent,
#         'relation_type': relation.relation_type,
#         'ai_name_called': relation.ai_name_called,
#     }

#     serializer = UserWithParentSerializer(data)
#     return Response(serializer.data, status=status.HTTP_200_OK)

# 1번 - User가 '설정' 페이지에서 정보들을 일부 수정할 때
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_user_settings(request):
    user = request.user
    
    try:
        relation = UserParentRelation.objects.select_related('parent').get(user=user)
    except UserParentRelation.DoesNotExist:
        return Response({'error': 'Parent not found.'}, status=status.HTTP_404_NOT_FOUND)

    user_serializer = UserSerializer(user, data=request.data.get('user', {}), partial=True)
    parent_serializer = ParentSerializer(relation.parent, data=request.data.get('parent', {}), partial=True)

    if user_serializer.is_valid() and parent_serializer.is_valid():
        user_serializer.save()
        parent_serializer.save()
        return Response({
            'user': user_serializer.data,
            'parent': parent_serializer.data,
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'user_errors': user_serializer.errors,
            'parent_errors': parent_serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    
# MyHome 들어갔을 때 로그인 되어 있는 User와 그의 어르신 정보 GET보내는 API
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

# 2번 - User가 '설정' 페이지에 들어갔을 때, User와 Parent의 신상 정보 반환하는 API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_parent_user_info(request):
    user = request.user  # 로그인된 보호자 (User)

    try:
        relation = UserParentRelation.objects.select_related('user', 'parent').get(user=user)
    except UserParentRelation.DoesNotExist:
        return Response({'error': 'Parent not found.'}, status=status.HTTP_404_NOT_FOUND)

    parent = relation.parent

    data = {
        "parent": {
            "name": parent.name,
            "birth_date": parent.birth_date,
            "sex": parent.get_sex_display(),
            "address": parent.address,
            "disease_info": parent.disease_info,
            "medication_info": parent.medication_info,
            "additional_notes": parent.additional_notes,
        },
        "guardian": {
            "username": user.username,
            "email": user.email,
            "phone_number": user.phone_number,
            "relation_type": relation.get_relation_type_display(),
            "ai_name_called": relation.ai_name_called,
        }
    }

    return Response(data, status=status.HTTP_200_OK)
