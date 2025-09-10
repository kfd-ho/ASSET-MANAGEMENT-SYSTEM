import os
import qrcode
from io import BytesIO
from django.db import models
from django.core.files import File
from decimal import Decimal
from PIL import Image
from apps.core.models import BaseModel, User


class Category(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    useful_life_years = models.PositiveIntegerField(default=5)
    depreciation_rate = models.DecimalField(
        max_digits=5, decimal_places=2, 
        default=Decimal('20.00'),
        help_text="Annual depreciation rate in percentage"
    )
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Asset(BaseModel):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('maintenance', 'Maintenance'),
        ('retired', 'Retired'),
        ('disposed', 'Disposed'),
    ]
    
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    serial_number = models.CharField(max_length=100, unique=True)
    purchase_date = models.DateField()
    cost = models.DecimalField(max_digits=12, decimal_places=2)
    current_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Asset details
    brand = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    specifications = models.TextField(blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    
    # Location
    location = models.CharField(max_length=200, blank=True)
    
    # Files
    photo = models.ImageField(upload_to='assets/photos/', null=True, blank=True)
    qr_code = models.ImageField(upload_to='assets/qr_codes/', null=True, blank=True)
    
    # Insurance
    insurance_policy = models.CharField(max_length=100, blank=True)
    insurance_expiry = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.serial_number})"
    
    def save(self, *args, **kwargs):
        # Calculate current value
        self.calculate_current_value()
        
        # Generate QR code if not exists
        if not self.qr_code:
            self.generate_qr_code()
        
        # Optimize photo if uploaded
        if self.photo:
            self.optimize_photo()
        
        super().save(*args, **kwargs)
    
    def calculate_current_value(self):
        """Calculate current depreciated value"""
        from datetime import date
        from dateutil.relativedelta import relativedelta
        
        if not self.purchase_date:
            self.current_value = self.cost
            return
        
        months_owned = relativedelta(date.today(), self.purchase_date).months
        years_owned = months_owned / 12
        
        if years_owned >= self.category.useful_life_years:
            self.current_value = Decimal('0.01') * self.cost  # 1% residual value
        else:
            annual_depreciation = self.cost * (self.category.depreciation_rate / 100)
            total_depreciation = annual_depreciation * Decimal(str(years_owned))
            self.current_value = max(
                self.cost - total_depreciation,
                Decimal('0.01') * self.cost
            )
    
    def generate_qr_code(self):
        """Generate QR code for the asset"""
        qr_data = f"Asset: {self.name}\nSerial: {self.serial_number}\nID: {self.id}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Save to BytesIO
        buffer = BytesIO()
        qr_image.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Save to model
        filename = f'qr_{self.serial_number}.png'
        self.qr_code.save(filename, File(buffer), save=False)
    
    def optimize_photo(self):
        """Optimize uploaded photo"""
        if not self.photo:
            return
        
        img = Image.open(self.photo)
        
        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Resize if too large
        max_size = (800, 600)
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save optimized image
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=85, optimize=True)
        buffer.seek(0)
        
        # Update the file
        filename = os.path.basename(self.photo.name)
        if not filename.lower().endswith('.jpg'):
            filename = os.path.splitext(filename)[0] + '.jpg'
        
        self.photo.save(filename, File(buffer), save=False)


class AssetDocument(BaseModel):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    document = models.FileField(upload_to='assets/documents/')
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.asset.name} - {self.title}"