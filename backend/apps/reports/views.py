import csv
import pandas as pd
from io import StringIO, BytesIO
from datetime import datetime, timedelta
from decimal import Decimal
from django.http import HttpResponse
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from apps.core.permissions import IsAdminOrManager
from apps.assets.models import Asset, Category
from apps.allocations.models import Allocation
from apps.maintenance.models import MaintenanceRecord
from apps.employees.models import Employee


@api_view(['GET'])
@permission_classes([IsAdminOrManager])
def dashboard_stats(request):
    """Get comprehensive dashboard statistics"""
    today = timezone.now().date()
    current_month = today.replace(day=1)
    current_year = today.replace(month=1, day=1)
    
    # Asset statistics
    total_assets = Asset.objects.count()
    active_assets = Asset.objects.filter(status='active').count()
    maintenance_assets = Asset.objects.filter(status='maintenance').count()
    retired_assets = Asset.objects.filter(status='retired').count()
    
    # Financial statistics
    total_asset_value = Asset.objects.aggregate(Sum('cost'))['cost__sum'] or 0
    current_asset_value = Asset.objects.aggregate(Sum('current_value'))['current_value__sum'] or 0
    depreciation_this_year = Asset.objects.filter(
        purchase_date__gte=current_year
    ).aggregate(
        total_depreciation=Sum('cost') - Sum('current_value')
    )['total_depreciation'] or 0
    
    # Allocation statistics
    total_allocations = Allocation.objects.count()
    active_allocations = Allocation.objects.filter(returned_at__isnull=True).count()
    allocations_this_month = Allocation.objects.filter(
        allocated_at__gte=current_month
    ).count()
    
    # Maintenance statistics
    maintenance_this_month = MaintenanceRecord.objects.filter(
        scheduled_date__gte=current_month
    ).count()
    maintenance_cost_this_year = MaintenanceRecord.objects.filter(
        completed_at__gte=current_year
    ).aggregate(Sum('actual_cost'))['actual_cost__sum'] or 0
    
    # Employee statistics
    total_employees = Employee.objects.filter(is_active=True).count()
    employees_with_assets = Allocation.objects.filter(
        returned_at__isnull=True
    ).values('employee').distinct().count()
    
    # Category breakdown
    category_stats = list(Asset.objects.values('category__name').annotate(
        count=Count('id'),
        total_value=Sum('cost'),
        current_value=Sum('current_value')
    ).order_by('-count'))
    
    # Monthly trends (last 12 months)
    monthly_trends = []
    for i in range(12):
        month_start = (current_month - timedelta(days=30*i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        monthly_trends.append({
            'month': month_start.strftime('%Y-%m'),
            'assets_purchased': Asset.objects.filter(
                purchase_date__gte=month_start,
                purchase_date__lte=month_end
            ).count(),
            'allocations': Allocation.objects.filter(
                allocated_at__gte=month_start,
                allocated_at__lte=month_end
            ).count(),
            'maintenance_cost': MaintenanceRecord.objects.filter(
                completed_at__gte=month_start,
                completed_at__lte=month_end
            ).aggregate(Sum('actual_cost'))['actual_cost__sum'] or 0
        })
    
    return Response({
        'assets': {
            'total': total_assets,
            'active': active_assets,
            'maintenance': maintenance_assets,
            'retired': retired_assets,
            'total_value': total_asset_value,
            'current_value': current_asset_value,
            'depreciation_this_year': depreciation_this_year
        },
        'allocations': {
            'total': total_allocations,
            'active': active_allocations,
            'this_month': allocations_this_month
        },
        'maintenance': {
            'this_month': maintenance_this_month,
            'cost_this_year': maintenance_cost_this_year
        },
        'employees': {
            'total': total_employees,
            'with_assets': employees_with_assets
        },
        'category_breakdown': category_stats,
        'monthly_trends': list(reversed(monthly_trends))
    })


@api_view(['GET'])
@permission_classes([IsAdminOrManager])
def depreciation_report(request):
    """Generate depreciation report"""
    year = request.GET.get('year', timezone.now().year)
    
    try:
        year = int(year)
    except ValueError:
        return Response({'error': 'Invalid year'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get assets purchased before or during the year
    assets = Asset.objects.filter(
        purchase_date__year__lte=year
    ).select_related('category')
    
    depreciation_data = []
    total_original_value = Decimal('0.00')
    total_current_value = Decimal('0.00')
    total_depreciation = Decimal('0.00')
    
    for asset in assets:
        # Calculate depreciation for the specific year
        original_value = asset.cost
        current_value = asset.current_value
        depreciation = original_value - current_value
        
        depreciation_data.append({
            'asset_id': asset.id,
            'asset_name': asset.name,
            'serial_number': asset.serial_number,
            'category': asset.category.name,
            'purchase_date': asset.purchase_date,
            'original_value': original_value,
            'current_value': current_value,
            'depreciation': depreciation,
            'depreciation_rate': asset.category.depreciation_rate
        })
        
        total_original_value += original_value
        total_current_value += current_value
        total_depreciation += depreciation
    
    return Response({
        'year': year,
        'summary': {
            'total_assets': len(depreciation_data),
            'total_original_value': total_original_value,
            'total_current_value': total_current_value,
            'total_depreciation': total_depreciation
        },
        'assets': depreciation_data
    })


@api_view(['GET'])
@permission_classes([IsAdminOrManager])
def allocation_report(request):
    """Generate allocation report"""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    employee_id = request.GET.get('employee')
    
    allocations = Allocation.objects.select_related('asset', 'employee').all()
    
    if start_date:
        allocations = allocations.filter(allocated_at__gte=start_date)
    if end_date:
        allocations = allocations.filter(allocated_at__lte=end_date)
    if employee_id:
        allocations = allocations.filter(employee_id=employee_id)
    
    allocation_data = []
    for allocation in allocations:
        duration = None
        if allocation.returned_at:
            duration = (allocation.returned_at.date() - allocation.allocated_at.date()).days
        
        allocation_data.append({
            'id': allocation.id,
            'asset_name': allocation.asset.name,
            'asset_serial': allocation.asset.serial_number,
            'employee_name': allocation.employee.get_full_name(),
            'employee_id': getattr(allocation.employee, 'employee', {}).employee_id if hasattr(allocation.employee, 'employee') else '',
            'allocated_at': allocation.allocated_at,
            'returned_at': allocation.returned_at,
            'duration_days': duration,
            'condition_at_allocation': allocation.condition_at_allocation,
            'condition_at_return': allocation.condition_at_return,
            'is_active': allocation.returned_at is None
        })
    
    return Response({
        'total_allocations': len(allocation_data),
        'active_allocations': len([a for a in allocation_data if a['is_active']]),
        'returned_allocations': len([a for a in allocation_data if not a['is_active']]),
        'allocations': allocation_data
    })


@api_view(['GET'])
@permission_classes([IsAdminOrManager])
def export_assets_csv(request):
    """Export assets to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="assets_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Name', 'Category', 'Serial Number', 'Purchase Date',
        'Cost (INR)', 'Current Value (INR)', 'Status', 'Brand', 'Model',
        'Location', 'Warranty Expiry'
    ])
    
    assets = Asset.objects.select_related('category').all()
    for asset in assets:
        writer.writerow([
            asset.id,
            asset.name,
            asset.category.name,
            asset.serial_number,
            asset.purchase_date,
            asset.cost,
            asset.current_value,
            asset.status,
            asset.brand,
            asset.model,
            asset.location,
            asset.warranty_expiry
        ])
    
    return response


@api_view(['POST'])
@permission_classes([IsAdminOrManager])
def import_assets_csv(request):
    """Import assets from CSV"""
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    csv_file = request.FILES['file']
    
    try:
        # Read CSV file
        decoded_file = csv_file.read().decode('utf-8')
        csv_data = csv.DictReader(StringIO(decoded_file))
        
        created_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_data, start=2):
            try:
                # Get or create category
                category_name = row.get('Category', '').strip()
                if not category_name:
                    errors.append(f"Row {row_num}: Category is required")
                    continue
                
                category, _ = Category.objects.get_or_create(
                    name=category_name,
                    defaults={'description': f'Imported category: {category_name}'}
                )
                
                # Create asset
                asset = Asset.objects.create(
                    name=row.get('Name', '').strip(),
                    category=category,
                    serial_number=row.get('Serial Number', '').strip(),
                    purchase_date=datetime.strptime(row.get('Purchase Date', ''), '%Y-%m-%d').date(),
                    cost=Decimal(row.get('Cost (INR)', '0')),
                    status=row.get('Status', 'active').lower(),
                    brand=row.get('Brand', '').strip(),
                    model=row.get('Model', '').strip(),
                    location=row.get('Location', '').strip(),
                    created_by=request.user
                )
                
                # Set warranty expiry if provided
                warranty_expiry = row.get('Warranty Expiry', '').strip()
                if warranty_expiry:
                    asset.warranty_expiry = datetime.strptime(warranty_expiry, '%Y-%m-%d').date()
                    asset.save()
                
                created_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        return Response({
            'message': f'Successfully imported {created_count} assets',
            'created_count': created_count,
            'errors': errors
        })
        
    except Exception as e:
        return Response({'error': f'Failed to process CSV file: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAdminOrManager])
def maintenance_cost_report(request):
    """Generate maintenance cost report"""
    year = request.GET.get('year', timezone.now().year)
    
    try:
        year = int(year)
    except ValueError:
        return Response({'error': 'Invalid year'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Monthly maintenance costs
    monthly_costs = []
    for month in range(1, 13):
        month_start = datetime(year, month, 1).date()
        if month == 12:
            month_end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            month_end = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        cost = MaintenanceRecord.objects.filter(
            completed_at__gte=month_start,
            completed_at__lte=month_end
        ).aggregate(Sum('actual_cost'))['actual_cost__sum'] or 0
        
        monthly_costs.append({
            'month': month_start.strftime('%Y-%m'),
            'cost': cost
        })
    
    # Cost by category
    category_costs = list(MaintenanceRecord.objects.filter(
        completed_at__year=year
    ).values('asset__category__name').annotate(
        total_cost=Sum('actual_cost'),
        count=Count('id')
    ).order_by('-total_cost'))
    
    # Total cost
    total_cost = MaintenanceRecord.objects.filter(
        completed_at__year=year
    ).aggregate(Sum('actual_cost'))['actual_cost__sum'] or 0
    
    return Response({
        'year': year,
        'total_cost': total_cost,
        'monthly_costs': monthly_costs,
        'category_costs': category_costs
    })