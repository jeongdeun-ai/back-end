from django.urls import path
from accounts.views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register-single/', UserRegister_single_APIView.as_view(), name='register'), # User만 혼자 가입하는 경우
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register-parent-late/',register_parent_late, name='register-parent-late'), # Parent만 따로 나중에 등록하는 경우
    # path('register-together/', )  # User가 가입하면서 동시에 Parent도 등록하는 경우
]  
