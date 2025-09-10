from django.urls import path
from . import views

urlpatterns = [
    path('schedules/', views.MaintenanceScheduleListCreateView.as_view(), name='schedule-list-create'),
    path('schedules/<int:pk>/', views.MaintenanceScheduleRetrieveUpdateDestroyView.as_view(), name='schedule-detail'),
    
    path('records/', views.MaintenanceRecordListCreateView.as_view(), name='record-list-create'),
    path('records/<int:pk>/', views.MaintenanceRecordRetrieveUpdateDestroyView.as_view(), name='record-detail'),
    
    path('warranty-alerts/', views.WarrantyAlertListView.as_view(), name='warranty-alerts'),
    path('warranty-alerts/send/', views.send_warranty_alerts, name='send-warranty-alerts'),
    
    path('stats/', views.maintenance_stats, name='maintenance-stats'),
    path('overdue/', views.overdue_maintenance, name='overdue-maintenance'),
]