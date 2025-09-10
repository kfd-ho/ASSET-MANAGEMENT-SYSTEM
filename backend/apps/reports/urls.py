from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_stats, name='dashboard-stats'),
    path('depreciation/', views.depreciation_report, name='depreciation-report'),
    path('allocation/', views.allocation_report, name='allocation-report'),
    path('maintenance-cost/', views.maintenance_cost_report, name='maintenance-cost-report'),
    
    # CSV Export/Import
    path('export/assets/', views.export_assets_csv, name='export-assets-csv'),
    path('import/assets/', views.import_assets_csv, name='import-assets-csv'),
]