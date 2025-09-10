from rest_framework import serializers
from .models import Category, Asset, AssetDocument


class CategorySerializer(serializers.ModelSerializer):
    asset_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'useful_life_years', 
                 'depreciation_rate', 'asset_count', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_asset_count(self, obj):
        return obj.asset_set.count()


class AssetDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetDocument
        fields = ['id', 'title', 'document', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class AssetListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    assigned_to = serializers.SerializerMethodField()
    
    class Meta:
        model = Asset
        fields = ['id', 'name', 'category_name', 'serial_number', 
                 'status', 'current_value', 'assigned_to', 'location']
    
    def get_assigned_to(self, obj):
        allocation = getattr(obj, 'current_allocation', None)
        if allocation:
            return {
                'id': allocation.employee.id,
                'name': allocation.employee.get_full_name(),
                'employee_id': allocation.employee.employee_id
            }
        return None


class AssetDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    documents = AssetDocumentSerializer(many=True, read_only=True)
    assigned_to = serializers.SerializerMethodField()
    allocation_history = serializers.SerializerMethodField()
    
    class Meta:
        model = Asset
        fields = ['id', 'name', 'category', 'category_id', 'serial_number',
                 'purchase_date', 'cost', 'current_value', 'status',
                 'brand', 'model', 'specifications', 'warranty_expiry',
                 'location', 'photo', 'qr_code', 'insurance_policy',
                 'insurance_expiry', 'documents', 'assigned_to',
                 'allocation_history', 'created_at', 'updated_at']
        read_only_fields = ['id', 'current_value', 'qr_code', 'created_at', 'updated_at']
    
    def get_assigned_to(self, obj):
        from apps.allocations.models import Allocation
        try:
            allocation = Allocation.objects.get(asset=obj, returned_at__isnull=True)
            return {
                'id': allocation.employee.id,
                'name': allocation.employee.get_full_name(),
                'employee_id': allocation.employee.employee_id,
                'allocated_at': allocation.allocated_at
            }
        except Allocation.DoesNotExist:
            return None
    
    def get_allocation_history(self, obj):
        from apps.allocations.models import Allocation
        allocations = Allocation.objects.filter(asset=obj).order_by('-allocated_at')[:5]
        return [{
            'employee_name': allocation.employee.get_full_name(),
            'employee_id': allocation.employee.employee_id,
            'allocated_at': allocation.allocated_at,
            'returned_at': allocation.returned_at,
            'notes': allocation.notes
        } for allocation in allocations]


class AssetCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ['name', 'category', 'serial_number', 'purchase_date',
                 'cost', 'status', 'brand', 'model', 'specifications',
                 'warranty_expiry', 'location', 'photo', 'insurance_policy',
                 'insurance_expiry']
    
    def validate_serial_number(self, value):
        instance = getattr(self, 'instance', None)
        if Asset.objects.exclude(pk=instance.pk if instance else None).filter(serial_number=value).exists():
            raise serializers.ValidationError("Asset with this serial number already exists.")
        return value