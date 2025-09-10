from rest_framework import serializers
from django.utils import timezone
from .models import MaintenanceSchedule, MaintenanceRecord, WarrantyAlert


class MaintenanceScheduleSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = MaintenanceSchedule
        fields = ['id', 'asset', 'asset_name', 'title', 'description', 'frequency',
                 'next_due_date', 'estimated_cost', 'assigned_to', 'assigned_to_name',
                 'is_active', 'overdue', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_overdue(self, obj):
        return obj.next_due_date < timezone.now().date()


class MaintenanceRecordListSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    days_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = MaintenanceRecord
        fields = ['id', 'asset_name', 'title', 'status', 'priority', 'scheduled_date',
                 'assigned_to_name', 'estimated_cost', 'actual_cost', 'days_overdue']
    
    def get_days_overdue(self, obj):
        if obj.status in ['completed', 'cancelled']:
            return 0
        today = timezone.now().date()
        if obj.scheduled_date < today:
            return (today - obj.scheduled_date).days
        return 0


class MaintenanceRecordDetailSerializer(serializers.ModelSerializer):
    asset_details = serializers.SerializerMethodField()
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    
    class Meta:
        model = MaintenanceRecord
        fields = ['id', 'asset_details', 'schedule', 'title', 'description', 'status',
                 'priority', 'scheduled_date', 'started_at', 'completed_at',
                 'assigned_to', 'assigned_to_name', 'performed_by', 'estimated_cost',
                 'actual_cost', 'work_performed', 'parts_used', 'next_maintenance_notes',
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_asset_details(self, obj):
        return {
            'id': obj.asset.id,
            'name': obj.asset.name,
            'serial_number': obj.asset.serial_number,
            'category': obj.asset.category.name,
            'status': obj.asset.status
        }


class WarrantyAlertSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    asset_serial = serializers.CharField(source='asset.serial_number', read_only=True)
    warranty_expiry = serializers.DateField(source='asset.warranty_expiry', read_only=True)
    
    class Meta:
        model = WarrantyAlert
        fields = ['id', 'asset_name', 'asset_serial', 'warranty_expiry', 'alert_date',
                 'days_before_expiry', 'is_sent', 'created_at']
        read_only_fields = ['id', 'created_at']