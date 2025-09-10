from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', views.CategoryRetrieveUpdateDestroyView.as_view(), name='category-detail'),
    
    path('', views.AssetListCreateView.as_view(), name='asset-list-create'),
    path('<int:pk>/', views.AssetRetrieveUpdateDestroyView.as_view(), name='asset-detail'),
    path('<int:asset_id>/documents/', views.AssetDocumentListCreateView.as_view(), name='asset-documents'),
    
    path('stats/', views.asset_stats, name='asset-stats'),
    path('search/', views.search_assets, name='asset-search'),
]