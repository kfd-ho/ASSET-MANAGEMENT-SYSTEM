from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from apps.core.models import User
from .models import Department, Employee


class DepartmentSerializer(serializers.ModelSerializer):
    employee_count = serializers.SerializerMethodField()
    manager_name = serializers.CharField(source='manager.get_full_name', read_only=True)
    full_path = serializers.CharField(read_only=True)
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'parent', 'manager', 
                 'manager_name', 'full_path', 'employee_count', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_employee_count(self, obj):
        return Employee.objects.filter(department=obj, is_active=True).count()


class EmployeeListSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    allocated_assets_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Employee
        fields = ['id', 'employee_id', 'name', 'email', 'department_name',
                 'designation', 'employment_type', 'is_active', 
                 'allocated_assets_count', 'join_date']


class EmployeeDetailSerializer(serializers.ModelSerializer):
    user_details = serializers.SerializerMethodField()
    department = DepartmentSerializer(read_only=True)
    reporting_manager_name = serializers.CharField(
        source='reporting_manager.get_full_name', read_only=True
    )
    allocated_assets = serializers.SerializerMethodField()
    
    class Meta:
        model = Employee
        fields = ['id', 'employee_id', 'user_details', 'department', 
                 'designation', 'join_date', 'reporting_manager', 
                 'reporting_manager_name', 'mobile', 'emergency_contact',
                 'address', 'employment_type', 'is_active', 'allocated_assets',
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_user_details(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'role': obj.user.role,
            'is_active': obj.user.is_active
        }
    
    def get_allocated_assets(self, obj):
        from apps.allocations.models import Allocation
        allocations = Allocation.objects.filter(
            employee=obj.user, 
            returned_at__isnull=True
        ).select_related('asset')
        
        return [{
            'asset_id': allocation.asset.id,
            'asset_name': allocation.asset.name,
            'serial_number': allocation.asset.serial_number,
            'allocated_at': allocation.allocated_at
        } for allocation in allocations]


class EmployeeCreateSerializer(serializers.ModelSerializer):
    # User fields
    username = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, default='employee')
    
    class Meta:
        model = Employee
        fields = ['username', 'email', 'first_name', 'last_name', 'password',
                 'role', 'employee_id', 'department', 'designation', 'join_date',
                 'reporting_manager', 'mobile', 'emergency_contact', 'address',
                 'employment_type']
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    
    def validate_employee_id(self, value):
        if Employee.objects.filter(employee_id=value).exists():
            raise serializers.ValidationError("Employee ID already exists")
        return value
    
    def create(self, validated_data):
        # Extract user data
        user_data = {
            'username': validated_data.pop('username'),
            'email': validated_data.pop('email'),
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name'),
            'role': validated_data.pop('role', 'employee')
        }
        password = validated_data.pop('password')
        
        # Create user
        user = User.objects.create_user(**user_data)
        user.set_password(password)
        user.save()
        
        # Create employee
        employee = Employee.objects.create(user=user, **validated_data)
        return employee


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    # User fields (optional updates)
    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, required=False)
    user_is_active = serializers.BooleanField(required=False)
    
    class Meta:
        model = Employee
        fields = ['email', 'first_name', 'last_name', 'role', 'user_is_active',
                 'department', 'designation', 'reporting_manager', 'mobile',
                 'emergency_contact', 'address', 'employment_type', 'is_active']
    
    def update(self, instance, validated_data):
        # Update user fields
        user = instance.user
        if 'email' in validated_data:
            user.email = validated_data.pop('email')
        if 'first_name' in validated_data:
            user.first_name = validated_data.pop('first_name')
        if 'last_name' in validated_data:
            user.last_name = validated_data.pop('last_name')
        if 'role' in validated_data:
            user.role = validated_data.pop('role')
        if 'user_is_active' in validated_data:
            user.is_active = validated_data.pop('user_is_active')
        user.save()
        
        # Update employee fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance