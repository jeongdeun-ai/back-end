from django.urls import path, include
from .views import *


urlpatterns = [
    path('add-event-for-parent/', add_event_for_parent, name='add-event-for-parent'), 
]
