from django.urls import path
from . import views

urlpatterns = [
    path('', views.AllocationListCreateView.as_view(), name='allocation-list-create'),
    path('<int:pk>/', views.AllocationRetrieveUpdateView.as_view(), name='allocation-detail'),
    path('<int:pk>/return/', views.return_asset, name='return-asset'),
    path('stats/', views.allocation_stats, name='allocation-stats'),
    path('my-allocations/', views.my_allocations, name='my-allocations'),
]