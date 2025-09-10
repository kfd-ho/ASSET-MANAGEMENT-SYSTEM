from django.db import models
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal
from apps.core.models import BaseModel, User
from apps.assets.models import Asset


class MaintenanceSchedule(BaseModel):
    FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annual', 'Semi-Annual'),
        ('annual', 'Annual'),
    ]
    
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='maintenance_schedules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    next_due_date = models.DateField()
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['next_due_date']
    
    def __str__(self):
        return f"{self.asset.name} - {self.title}"
    
    def update_next_due_date(self):
        """Update next due date based on frequency"""
        from dateutil.relativedelta import relativedelta
        
        if self.frequency == 'weekly':
            self.next_due_date += relativedelta(weeks=1)
        elif self.frequency == 'monthly':
            self.next_due_date += relativedelta(months=1)
        elif self.frequency == 'quarterly':
            self.next_due_date += relativedelta(months=3)
        elif self.frequency == 'semi_annual':
            self.next_due_date += relativedelta(months=6)
        elif self.frequency == 'annual':
            self.next_due_date += relativedelta(years=1)
        
        self.save()


class MaintenanceRecord(BaseModel):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='maintenance_records')
    schedule = models.ForeignKey(MaintenanceSchedule, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Dates
    scheduled_date = models.DateField()
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Personnel
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    performed_by = models.CharField(max_length=200, blank=True)
    
    # Costs
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Documentation
    work_performed = models.TextField(blank=True)
    parts_used = models.TextField(blank=True)
    next_maintenance_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"{self.asset.name} - {self.title} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Update asset status based on maintenance status
        if self.status == 'in_progress' and self.asset.status == 'active':
            self.asset.status = 'maintenance'
            self.asset.save()
        elif self.status == 'completed' and self.asset.status == 'maintenance':
            self.asset.status = 'active'
            self.asset.save()
        
        super().save(*args, **kwargs)
        
        # Update schedule next due date if completed
        if self.status == 'completed' and self.schedule:
            self.schedule.update_next_due_date()


class WarrantyAlert(BaseModel):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='warranty_alerts')
    alert_date = models.DateField()
    days_before_expiry = models.PositiveIntegerField(default=30)
    is_sent = models.BooleanField(default=False)
    sent_to = models.ManyToManyField(User, blank=True)
    
    class Meta:
        ordering = ['alert_date']
        unique_together = ['asset', 'days_before_expiry']
    
    def __str__(self):
        return f"Warranty Alert: {self.asset.name} - {self.days_before_expiry} days"
    
    def send_alert(self):
        """Send warranty expiry alert"""
        if self.is_sent:
            return
        
        try:
            subject = f'Warranty Expiry Alert: {self.asset.name}'
            message = f"""
Asset Warranty Expiry Alert

Asset: {self.asset.name}
Serial Number: {self.asset.serial_number}
Warranty Expiry Date: {self.asset.warranty_expiry}
Days Remaining: {self.days_before_expiry}

Please take necessary action to renew or extend the warranty.

Asset Management System
            """
            
            # Send to admin and managers
            recipients = User.objects.filter(role__in=['admin', 'manager']).values_list('email', flat=True)
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                list(recipients),
                fail_silently=True,
            )
            
            self.is_sent = True
            self.sent_to.set(User.objects.filter(role__in=['admin', 'manager']))
            self.save()
            
        except Exception as e:
            print(f"Failed to send warranty alert: {e}")