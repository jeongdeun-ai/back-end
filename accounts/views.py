from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from accounts.serializers import UserRegisterSingleUserRegisterSerializer

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

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
# from .models import User

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # 유저 정보도 함께 반환
        data.update({
            "username": self.user.username,
            "email": self.user.email,
            "phone_number": self.user.phone_number,
        })

        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer



# User 객체 혼자 회원가입 하는 코드
class UserRegister_single_APIView(APIView):
    def post(self, request):
        serializer = UserRegisterSingleUserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': '회원가입 성공'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 기 회원인 User 객체가 추가적으로 자신의 Parent 객체를 생성시키고 relation 객체로 연결하는 API

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_parent_late(request):
    user = request.user # JWT 인증된 User 객체 추출
    
    data = request.data

    # 이미 부모 등록한 User -> 400 에러
    if UserParentRelation.objects.filter(user = user).exists():
        return Response({"error" : "이미 부모를 등록한 보호자입니다. 부모를 중복하여 등록할 수 없습니다."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Parent 객체 생성
        parent = Parent.objects.create(
            name = data.get('name'),
            birth_date = data.get('birth_date'),
            disease_info = data.get("disease_info", ''),
            medication_info = data.get('medication_info', ''),
            additional_notes = data.get('additional_notes', ''),
        )

        # Relation 생성
        UserParentRelation.objects.create(user=user, parent=parent)

        return Response({'message' : "부모님 정보 등록 및 연결 완료."}, status = status.HTTP_201_CREATED)
    except IntegrityError:
        return Response({'error':'데이터 저장 중 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


from storages.backends.s3boto3 import S3Boto3Storage
# 회원가입할 때 아예 User 정보랑 Parent 정보 동시에 입력받고 연결까지 다 하는 API (얘로 사용)
import boto3
import uuid
from django.core.files.uploadedfile import UploadedFile

@api_view(['POST'])
def register_user_and_parent_together(request):
    data = request.data
    photo_file = request.FILES.get('parent_photo')

    if not photo_file:
        return Response({'error': 'parent_photo 파일이 필요합니다.'}, status=400)

    try:
        # ✅ S3 클라이언트 생성
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )

        # ✅ 파일명 생성
        photo_filename = f"photos/{uuid.uuid4()}_{photo_file.name}"
        # photo_filename = f"speech/{uuid.uuid4()}_{photo_file.name}"

        # ✅ S3에 직접 업로드
        s3.put_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=photo_filename,
            Body=photo_file.read(),
            ContentType=photo_file.content_type,
            # ACL='public-read'  # ❌ 넣으면 안 됨
        )

        # ✅ URL 생성
        photo_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{photo_filename}"

        with transaction.atomic():  
            user = User(
                email=data.get('email'),
                username=data.get('username'),
                phone_number=data.get('phone_number'),
            )
            user.set_password(data.get('password'))
            user.save()

            parent = Parent.objects.create(
                name=data.get('parent_name'),
                birth_date=data.get('parent_birth_date'),
                sex=data.get('parent_sex'),
                photo=photo_url,  # ✅ S3 URL 저장
                address=data.get('parent_address', ''),
                disease_info=data.get('parent_disease_info', ''),
                medication_info=data.get('parent_medication_info', ''),
                additional_notes=data.get('parent_additional_notes', ''),
            )

            UserParentRelation.objects.create(
                user=user,
                parent=parent,
                relation_type=data.get('relation_type'),
                ai_name_called=data.get('ai_name_called')
            )

            sex_display = parent.get_sex_display() if parent.sex else "성별 미상"
            initial_context = f"{parent.name}님은 {parent.birth_date}생 {sex_display}이며, " \
                            f"주요 질환은 {parent.disease_info}이며, 복용 중인 약은 {parent.medication_info}입니다. " \
                            f"참고사항: {parent.additional_notes}"

            ContextSummary.objects.create(
                parent=parent,
                content=initial_context
            )

            return Response({'message': '회원가입 + 부모 등록 + 초기 ContextSummary 저장 완료'}, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# from storages.backends.s3boto3 import S3Boto3Storage
# # 회원가입할 때 아예 User 정보랑 Parent 정보 동시에 입력받고 연결까지 다 하는 API (얘로 사용)
# @api_view(['POST'])
# def register_user_and_parent_together(request):
#     data = request.data

#     print("✅ request.FILES:", request.FILES)

#     # 뷰 내부
#     s3_storage = S3Boto3Storage()

#     photo_file = request.FILES.get('parent_photo')
#     if not photo_file:
#         return Response({'error': 'parent_photo 파일이 필요합니다.'}, status=400)

#     photo_name = photo_file.name
#     photo_path_in_s3 = s3_storage.save(photo_name, photo_file)

#     try:
#         with transaction.atomic():  
#             # User 생성
#             user = User(
#                 email=data.get('email'),
#                 username=data.get('username'),
#                 phone_number=data.get('phone_number'),
#             )
#             user.set_password(data.get('password'))
#             user.save()

#             # Parent 생성
#             parent = Parent.objects.create(
#                 name=data.get('parent_name'),
#                 birth_date=data.get('parent_birth_date'),
#                 sex=data.get('parent_sex'),
#                 photo=photo_path_in_s3,  # ✅ 경로 문자열로 저장됨
#                 address=data.get('parent_address', ''),
#                 disease_info=data.get('parent_disease_info', ''),
#                 medication_info=data.get('parent_medication_info', ''),
#                 additional_notes=data.get('parent_additional_notes', ''),
#             )

#             # Relation 생성
#             UserParentRelation.objects.create(
#                 user=user,
#                 parent=parent,
#                 relation_type=data.get('relation_type'),
#                 ai_name_called=data.get('ai_name_called')
#             )

#             # 💡 ContextSummary에 초기 프로필 등록
#             sex_display = parent.get_sex_display() if parent.sex else "성별 미상"
#             initial_context = f"{parent.name}님은 {parent.birth_date}생 {sex_display}이며, " \
#                             f"주요 질환은 {parent.disease_info}이며, 복용 중인 약은 {parent.medication_info}입니다. " \
#                             f"참고사항: {parent.additional_notes}"

#             ContextSummary.objects.create(
#                 parent=parent,
#                 content=initial_context
#             )

#             return Response({'message': '회원가입 + 부모 등록 + 초기 ContextSummary 저장 완료'}, status=status.HTTP_201_CREATED)
#     except Exception as e:
#         return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)