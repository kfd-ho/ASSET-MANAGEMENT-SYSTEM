from rest_framework import serializers
from django.utils import timezone
from .models import Allocation, AllocationHistory


class AllocationListSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    asset_serial = serializers.CharField(source='asset.serial_number', read_only=True)
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee.employee_id', read_only=True)
    is_active = serializers.SerializerMethodField()
    duration_days = serializers.SerializerMethodField()
    
    class Meta:
        model = Allocation
        fields = ['id', 'asset_name', 'asset_serial', 'employee_name', 'employee_id',
                 'allocated_at', 'returned_at', 'is_active', 'duration_days',
                 'condition_at_allocation', 'condition_at_return']
    
    def get_is_active(self, obj):
        return obj.returned_at is None
    
    def get_duration_days(self, obj):
        end_date = obj.returned_at or timezone.now()
        return (end_date.date() - obj.allocated_at.date()).days


class AllocationDetailSerializer(serializers.ModelSerializer):
    asset_details = serializers.SerializerMethodField()
    employee_details = serializers.SerializerMethodField()
    history = serializers.SerializerMethodField()
    
    class Meta:
        model = Allocation
        fields = ['id', 'asset_details', 'employee_details', 'allocated_at',
                 'returned_at', 'notes', 'condition_at_allocation',
                 'condition_at_return', 'return_notes', 'history', 'created_at']
        read_only_fields = ['id', 'allocated_at', 'created_at']
    
    def get_asset_details(self, obj):
        return {
            'id': obj.asset.id,
            'name': obj.asset.name,
            'serial_number': obj.asset.serial_number,
            'category': obj.asset.category.name,
            'current_value': obj.asset.current_value
        }
    
    def get_employee_details(self, obj):
        return {
            'id': obj.employee.id,
            'name': obj.employee.get_full_name(),
            'employee_id': getattr(obj.employee, 'employee', {}).employee_id if hasattr(obj.employee, 'employee') else '',
            'email': obj.employee.email,
            'department': getattr(obj.employee, 'employee', {}).department.name if hasattr(obj.employee, 'employee') else ''
        }
    
    def get_history(self, obj):
        history = AllocationHistory.objects.filter(allocation=obj)[:10]
        return [{
            'action': h.action,
            'details': h.details,
            'created_at': h.created_at,
            'created_by': h.created_by.get_full_name() if h.created_by else None
        } for h in history]


class AllocationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Allocation
        fields = ['asset', 'employee', 'notes', 'condition_at_allocation']
    
    def validate_asset(self, value):
        # Check if asset is already allocated
        if Allocation.objects.filter(asset=value, returned_at__isnull=True).exists():
            raise serializers.ValidationError("Asset is already allocated to someone else")
        
        # Check if asset is available for allocation
        if value.status not in ['active']:
            raise serializers.ValidationError("Asset is not available for allocation")
        
        return value
    
    def create(self, validated_data):
        allocation = super().create(validated_data)
        
        # Create history entry
        AllocationHistory.objects.create(
            allocation=allocation,
            action='allocated',
            details={
                'asset': allocation.asset.name,
                'employee': allocation.employee.get_full_name(),
                'condition': allocation.condition_at_allocation
            },
            created_by=self.context['request'].user
        )
        
        return allocation


class AllocationReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Allocation
        fields = ['condition_at_return', 'return_notes']
    
    def update(self, instance, validated_data):
        instance.returned_at = timezone.now()
        instance.condition_at_return = validated_data.get('condition_at_return')
        instance.return_notes = validated_data.get('return_notes', '')
        instance.save()
        
        # Send return email
        instance.send_return_email()
        
        # Create history entry
        AllocationHistory.objects.create(
            allocation=instance,
            action='returned',
            details={
                'return_condition': instance.get_condition_at_return_display(),
                'return_notes': instance.return_notes
            },
            created_by=self.context['request'].user
        )
        
        return instance