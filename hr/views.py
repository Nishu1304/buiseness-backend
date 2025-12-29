from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core.mixins import TenantViewSetMixin
from core.permissions import IsTenantUser

from .models import Staff, Attendance
from .serializers import StaffSerializer, AttendanceSerializer


class StaffViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for Staff CRUD operations with tenant isolation.
    
    Endpoints:
    - GET /api/hr/staff/ - List all staff members
    - POST /api/hr/staff/ - Create new staff member
    - GET /api/hr/staff/{id}/ - Get staff details
    - PUT/PATCH /api/hr/staff/{id}/ - Update staff
    - DELETE /api/hr/staff/{id}/ - Delete staff
    """
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantUser]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = ['name', 'position', 'phone']
    ordering_fields = ['name', 'joining_date', 'salary', 'created_at']
    filterset_fields = ['position', 'is_active']
    ordering = ['name']

    def perform_create(self, serializer):
        """Automatically set tenant from request."""
        serializer.save(tenant=self.request.tenant)

    @action(detail=True, methods=['GET'], url_path='attendance-history')
    def attendance_history(self, request, pk=None):
        """Get attendance history for a specific staff member."""
        staff = self.get_object()
        attendance_records = staff.attendance_records.order_by('-date')
        serializer = AttendanceSerializer(attendance_records, many=True)
        return Response(serializer.data)


class AttendanceViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for Attendance CRUD operations with tenant isolation.
    
    Endpoints:
    - GET /api/hr/attendance/ - List all attendance records
    - POST /api/hr/attendance/ - Mark attendance
    - GET /api/hr/attendance/{id}/ - Get attendance details
    - PUT/PATCH /api/hr/attendance/{id}/ - Update attendance
    - DELETE /api/hr/attendance/{id}/ - Delete attendance
    """
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantUser]
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
    ]
    filterset_fields = ['staff', 'date', 'status']
    ordering_fields = ['date', 'created_at']
    ordering = ['-date']

    def perform_create(self, serializer):
        """Automatically set tenant from request."""
        serializer.save(tenant=self.request.tenant)

    def create(self, request, *args, **kwargs):
        """
        Create or update attendance for a staff member on a specific date.
        If attendance already exists for the staff on that date, update it.
        """
        staff_id = request.data.get('staffId')
        date = request.data.get('date')
        
        # Check if attendance already exists for this staff and date
        existing = Attendance.objects.filter(
            staff_id=staff_id,
            date=date,
            tenant=request.tenant
        ).first()
        
        if existing:
            # Update existing attendance
            serializer = self.get_serializer(existing, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        # Create new attendance
        return super().create(request, *args, **kwargs)
