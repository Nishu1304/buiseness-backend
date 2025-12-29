from rest_framework import serializers
from .models import Staff, Attendance


class StaffSerializer(serializers.ModelSerializer):
    """Serializer for Staff model with frontend-compatible field names."""
    aadhaarFileName = serializers.SerializerMethodField()
    # Accept both 'joiningDate' (JSON) and 'joining_date' (FormData)
    joiningDate = serializers.DateField(source='joining_date', required=False)
    joining_date = serializers.DateField(required=False, write_only=True)
    
    class Meta:
        model = Staff
        fields = [
            'staff_id',
            'name',
            'position',
            'phone',
            'email',
            'joiningDate',
            'joining_date',  # Accept underscore version from FormData
            'salary',
            'aadhaar_file',
            'aadhaarFileName',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['staff_id', 'created_at', 'updated_at', 'aadhaarFileName']
        extra_kwargs = {
            'aadhaar_file': {'write_only': True, 'required': False}
        }
    
    def get_aadhaarFileName(self, obj):
        """Return just the filename from the aadhaar_file field."""
        if obj.aadhaar_file:
            return obj.aadhaar_file.name.split('/')[-1]
        return None
    
    def validate(self, data):
        """Handle both joiningDate and joining_date field names."""
        # If joining_date came via underscore format, it's already in data
        # If joiningDate came, it was mapped to joining_date via source
        # Either way, we need to ensure joining_date is present
        
        if 'joining_date' not in data and self.initial_data.get('joining_date'):
            # FormData sends joining_date directly
            pass  # Will be handled by the field
        
        return data
    
    def to_internal_value(self, data):
        """Convert incoming data to internal format."""
        # Handle both field name formats
        mutable_data = data.copy() if hasattr(data, 'copy') else dict(data)
        
        # If joining_date is in data but joiningDate is not, copy it
        if 'joining_date' in mutable_data and 'joiningDate' not in mutable_data:
            mutable_data['joiningDate'] = mutable_data['joining_date']
        
        return super().to_internal_value(mutable_data)


class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer for Attendance model with frontend-compatible field names."""
    staffId = serializers.PrimaryKeyRelatedField(
        source='staff', 
        queryset=Staff.objects.all()
    )
    staff_name = serializers.CharField(source='staff.name', read_only=True)
    
    class Meta:
        model = Attendance
        fields = [
            'attendance_id',
            'staffId',
            'staff_name',
            'date',
            'status',
            'created_at'
        ]
        read_only_fields = ['attendance_id', 'created_at', 'staff_name']

    def validate(self, data):
        """Validate that staff belongs to the same tenant."""
        request = self.context.get('request')
        if request and hasattr(request, 'tenant'):
            staff = data.get('staff')
            if staff and staff.tenant != request.tenant:
                raise serializers.ValidationError(
                    "Staff member must belong to your tenant."
                )
        return data
