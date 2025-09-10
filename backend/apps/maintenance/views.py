from rest_framework import generics, filters, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from apps.core.permissions import IsAdminOrManagerOrReadOnly
from .models import MaintenanceSchedule, MaintenanceRecord, WarrantyAlert
from .serializers import (
    MaintenanceScheduleSerializer, MaintenanceRecordListSerializer,
    MaintenanceRecordDetailSerializer, WarrantyAlertSerializer
)


class MaintenanceScheduleListCreateView(generics.ListCreateAPIView):
    queryset = MaintenanceSchedule.objects.select_related('asset', 'assigned_to').all()
    serializer_class = MaintenanceScheduleSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'asset__name', 'asset__serial_number']
    filterset_fields = ['asset__category', 'frequency', 'assigned_to', 'is_active']
    ordering_fields = ['next_due_date', 'created_at']
    ordering = ['next_due_date']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class MaintenanceScheduleRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MaintenanceSchedule.objects.select_related('asset', 'assigned_to').all()
    serializer_class = MaintenanceScheduleSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class MaintenanceRecordListCreateView(generics.ListCreateAPIView):
    queryset = MaintenanceRecord.objects.select_related('asset', 'assigned_to').all()
    permission_classes = [IsAdminOrManagerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'asset__name', 'asset__serial_number']
    filterset_fields = ['asset__category', 'status', 'priority', 'assigned_to']
    ordering_fields = ['scheduled_date', 'created_at', 'priority']
    ordering = ['-scheduled_date']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MaintenanceRecordDetailSerializer
        return MaintenanceRecordListSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class MaintenanceRecordRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MaintenanceRecord.objects.select_related('asset', 'assigned_to').all()
    serializer_class = MaintenanceRecordDetailSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    
    def perform_update(self, serializer):
        # Update timestamps based on status
        instance = serializer.instance
        new_status = serializer.validated_data.get('status', instance.status)
        
        if new_status == 'in_progress' and not instance.started_at:
            serializer.validated_data['started_at'] = timezone.now()
        elif new_status == 'completed' and not instance.completed_at:
            serializer.validated_data['completed_at'] = timezone.now()
        
        serializer.save(updated_by=self.request.user)


class WarrantyAlertListView(generics.ListAPIView):
    queryset = WarrantyAlert.objects.select_related('asset').all()
    serializer_class = WarrantyAlertSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_sent', 'days_before_expiry']
    ordering = ['alert_date']


@api_view(['GET'])
def maintenance_stats(request):
    """Get maintenance statistics"""
    today = timezone.now().date()
    
    stats = {
        'total_schedules': MaintenanceSchedule.objects.filter(is_active=True).count(),
        'overdue_schedules': MaintenanceSchedule.objects.filter(
            is_active=True, next_due_date__lt=today
        ).count(),
        'upcoming_schedules': MaintenanceSchedule.objects.filter(
            is_active=True, next_due_date__gte=today, next_due_date__lte=today + timezone.timedelta(days=30)
        ).count(),
        'total_records': MaintenanceRecord.objects.count(),
        'pending_records': MaintenanceRecord.objects.filter(status__in=['scheduled', 'in_progress']).count(),
        'completed_this_month': MaintenanceRecord.objects.filter(
            status='completed',
            completed_at__year=today.year,
            completed_at__month=today.month
        ).count(),
        'total_cost_this_year': MaintenanceRecord.objects.filter(
            completed_at__year=today.year
        ).aggregate(Sum('actual_cost'))['actual_cost__sum'] or 0,
        'avg_cost_per_maintenance': MaintenanceRecord.objects.filter(
            status='completed'
        ).aggregate(Avg('actual_cost'))['actual_cost__avg'] or 0,
        'warranty_alerts': WarrantyAlert.objects.filter(is_sent=False).count(),
    }
    return Response(stats)


@api_view(['GET'])
def overdue_maintenance(request):
    """Get overdue maintenance items"""
    today = timezone.now().date()
    
    # Overdue schedules
    overdue_schedules = MaintenanceSchedule.objects.filter(
        is_active=True, next_due_date__lt=today
    ).select_related('asset')
    
    # Overdue records
    overdue_records = MaintenanceRecord.objects.filter(
        status__in=['scheduled', 'in_progress'],
        scheduled_date__lt=today
    ).select_related('asset')
    
    return Response({
        'overdue_schedules': MaintenanceScheduleSerializer(overdue_schedules, many=True).data,
        'overdue_records': MaintenanceRecordListSerializer(overdue_records, many=True).data,
    })


@api_view(['POST'])
def send_warranty_alerts(request):
    """Send pending warranty alerts"""
    alerts = WarrantyAlert.objects.filter(is_sent=False)
    sent_count = 0
    
    for alert in alerts:
        alert.send_alert()
        sent_count += 1
    
    return Response({
        'message': f'Sent {sent_count} warranty alerts',
        'sent_count': sent_count
    })