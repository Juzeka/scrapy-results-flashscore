from django.urls import path
from bot.views import BotResultsInLiveViewSet


urlpatterns = [
    path('', BotResultsInLiveViewSet.as_view({'get': 'list'}))
]
