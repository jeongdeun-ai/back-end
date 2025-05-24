from django.urls import path, include
from .views import *

urlpatterns = [
    path('gpt-ask-parent/', gpt_ask_parent, name='gpt-ask-parent'), # 1번 뷰 url
    path('parent-reply-to_gpt/', parent_reply_to_gpt, name='parent-reply-to-gpt'), # 4번
]