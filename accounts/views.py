from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from accounts.serializers import UserRegisterSingleUserRegisterSerializer

from table.models import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.db import IntegrityError

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
            birth_data = data.get('birth_data'),
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