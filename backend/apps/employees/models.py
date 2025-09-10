from django.db import models
from apps.core.models import BaseModel, User


class Department(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def full_path(self):
        """Get full department hierarchy path"""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name


class Employee(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    designation = models.CharField(max_length=100)
    join_date = models.DateField()
    reporting_manager = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='subordinates'
    )
    
    # Contact Information
    mobile = models.CharField(max_length=15, blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    
    # Employment Details
    employment_type = models.CharField(
        max_length=20,
        choices=[
            ('full_time', 'Full Time'),
            ('part_time', 'Part Time'),
            ('contract', 'Contract'),
            ('intern', 'Intern'),
        ],
        default='full_time'
    )
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['employee_id']
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"
    
    @property
    def allocated_assets_count(self):
        from apps.allocations.models import Allocation
        return Allocation.objects.filter(
            employee=self.user, 
            returned_at__isnull=True
        ).count()