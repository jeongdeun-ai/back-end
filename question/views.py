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

from datetime import date


# 1번 - Parent 객체의 ContextSummary와 오늘 대화 기록을 바탕으로 AI 추천 질문을 생성해주는 api
