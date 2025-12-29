from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StaffViewSet, AttendanceViewSet

router = DefaultRouter()
router.register(r'staff', StaffViewSet, basename='staff')
router.register(r'attendance', AttendanceViewSet, basename='attendance')

urlpatterns = [
    path('', include(router.urls)),
]
