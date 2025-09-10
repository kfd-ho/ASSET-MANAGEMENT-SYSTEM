from django.db import models
from django.core.mail import send_mail
from django.conf import settings
from apps.core.models import BaseModel, User
from apps.assets.models import Asset


class Allocation(BaseModel):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='allocations')
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='allocations')
    allocated_at = models.DateTimeField(auto_now_add=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    condition_at_allocation = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
        ],
        default='good'
    )
    condition_at_return = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
            ('damaged', 'Damaged'),
        ],
        null=True,
        blank=True
    )
    return_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-allocated_at']
        unique_together = ['asset', 'employee', 'allocated_at']
    
    def __str__(self):
        status = "Active" if not self.returned_at else "Returned"
        return f"{self.asset.name} → {self.employee.get_full_name()} ({status})"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Send email notification for new allocation
        if is_new:
            self.send_allocation_email()
    
    def send_allocation_email(self):
        """Send email notification for asset allocation"""
        try:
            subject = f'Asset Allocated: {self.asset.name}'
            message = f"""
Dear {self.employee.get_full_name()},

An asset has been allocated to you:

Asset: {self.asset.name}
Serial Number: {self.asset.serial_number}
Category: {self.asset.category.name}
Allocated Date: {self.allocated_at.strftime('%Y-%m-%d %H:%M')}
Condition: {self.get_condition_at_allocation_display()}

Notes: {self.notes}

Please take good care of this asset and report any issues immediately.

Best regards,
Asset Management Team
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.employee.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send allocation email: {e}")
    
    def send_return_email(self):
        """Send email notification for asset return"""
        try:
            subject = f'Asset Returned: {self.asset.name}'
            message = f"""
Dear {self.employee.get_full_name()},

Your asset return has been processed:

Asset: {self.asset.name}
Serial Number: {self.asset.serial_number}
Returned Date: {self.returned_at.strftime('%Y-%m-%d %H:%M')}
Return Condition: {self.get_condition_at_return_display()}

Return Notes: {self.return_notes}

Thank you for returning the asset in good condition.

Best regards,
Asset Management Team
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.employee.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send return email: {e}")


class AllocationHistory(BaseModel):
    """Audit trail for allocation changes"""
    allocation = models.ForeignKey(Allocation, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(
        max_length=20,
        choices=[
            ('allocated', 'Allocated'),
            ('returned', 'Returned'),
            ('updated', 'Updated'),
        ]
    )
    details = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Allocation histories"
    
    def __str__(self):
        return f"{self.allocation} - {self.action} at {self.created_at}"