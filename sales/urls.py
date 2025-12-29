from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet, BillViewSet, CustomerPaymentViewSet

router = DefaultRouter()
router.register("customers", CustomerViewSet, basename="customer")
router.register("bills", BillViewSet, basename="bill")
router.register("payments", CustomerPaymentViewSet, basename="payment")

urlpatterns = [
    path("", include(router.urls)),
]
