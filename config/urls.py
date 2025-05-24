from django.contrib import admin
from django.urls import path, include
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('chat/', include('chat.urls')),
    path('myhome/', include('myhome.urls')),
    path('record/', include('record.urls')),
    path('question/', include('question.urls')),
    path('schedule/', include('schedule.urls')),
    path('home/', include('home.urls')),
]
