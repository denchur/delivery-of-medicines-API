from django.urls import include, path, re_path
from rest_framework import routers
from .views import OrdersViewSet

api_router_v1 = routers.DefaultRouter()
api_router_v1.register('orders', OrdersViewSet)
urlpatterns = [
    path('', include(api_router_v1.urls)),
    path('', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.authtoken')),
]