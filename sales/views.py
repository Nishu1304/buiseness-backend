from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from core.mixins import TenantViewSetMixin
from core.permissions import IsTenantUser
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from .models import Customer, Bill, CustomerPayment
from .serializers import CustomerSerializer, BillCreateSerializer, BillDetailSerializer, CustomerPaymentSerializer


class CustomerViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsTenantUser]
    filter_backends = [SearchFilter]
    search_fields = ["phone"]


class BillViewSet(TenantViewSetMixin, viewsets.GenericViewSet):
    queryset = Bill.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {
        "date": ["gte", "lte"],
    }
    ordering_fields = ["date", "grand_total"]

    def get_serializer_class(self):
        if self.action == "create":
            return BillCreateSerializer
        else:
            return BillDetailSerializer

    def list(self, request):
        qs = self.filter_queryset(self.get_queryset())
        serializer = BillDetailSerializer(qs, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        bill = self.get_object()
        serializer = BillDetailSerializer(bill)
        return Response(serializer.data)

    def create(self, request):
        serializer = BillCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        bill = serializer.save()
        out = BillDetailSerializer(bill)
        return Response(out.data, status=status.HTTP_201_CREATED)


class CustomerPaymentViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    queryset = CustomerPayment.objects.all()
    serializer_class = CustomerPaymentSerializer
    permission_classes = [IsTenantUser]

    def perform_create(self, serializer):
        # Optionally update customer's spending_balance on payment
        payment = serializer.save()
        # If payment type is CREDIT (customer paying back), reduce spending_balance
        if payment.type and payment.type.upper() == "CREDIT":
            cust = payment.customer
            from django.db.models import F
            cust.spending_balance = F('spending_balance') - payment.amount
            cust.save(update_fields=['spending_balance'])
