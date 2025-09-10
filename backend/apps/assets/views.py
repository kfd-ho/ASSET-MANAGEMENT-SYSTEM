from rest_framework import generics, filters, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum
from apps.core.permissions import IsAdminOrManagerOrReadOnly
from .models import Category, Asset, AssetDocument
from .serializers import (
    CategorySerializer, AssetListSerializer, AssetDetailSerializer,
    AssetCreateUpdateSerializer, AssetDocumentSerializer
)


class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class CategoryRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class AssetListCreateView(generics.ListCreateAPIView):
    queryset = Asset.objects.select_related('category').all()
    permission_classes = [IsAdminOrManagerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'serial_number', 'brand', 'model']
    filterset_fields = ['category', 'status', 'location']
    ordering_fields = ['name', 'purchase_date', 'cost', 'current_value', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AssetCreateUpdateSerializer
        return AssetListSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AssetRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Asset.objects.select_related('category').prefetch_related('documents').all()
    permission_classes = [IsAdminOrManagerOrReadOnly]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return AssetCreateUpdateSerializer
        return AssetDetailSerializer
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class AssetDocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = AssetDocumentSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    
    def get_queryset(self):
        asset_id = self.kwargs.get('asset_id')
        return AssetDocument.objects.filter(asset_id=asset_id)
    
    def perform_create(self, serializer):
        asset_id = self.kwargs.get('asset_id')
        serializer.save(asset_id=asset_id, created_by=self.request.user)


@api_view(['GET'])
def asset_stats(request):
    """Get asset statistics"""
    stats = {
        'total_assets': Asset.objects.count(),
        'total_value': Asset.objects.aggregate(Sum('cost'))['cost__sum'] or 0,
        'current_value': Asset.objects.aggregate(Sum('current_value'))['current_value__sum'] or 0,
        'by_status': dict(Asset.objects.values('status').annotate(count=Count('id')).values_list('status', 'count')),
        'by_category': list(Asset.objects.values('category__name').annotate(
            count=Count('id'),
            total_value=Sum('cost')
        ).values('category__name', 'count', 'total_value'))
    }
    return Response(stats)


@api_view(['GET'])
def search_assets(request):
    """Search assets with advanced filtering"""
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')
    
    assets = Asset.objects.select_related('category').all()
    
    if query:
        assets = assets.filter(
            Q(name__icontains=query) |
            Q(serial_number__icontains=query) |
            Q(brand__icontains=query) |
            Q(model__icontains=query)
        )
    
    if category:
        assets = assets.filter(category_id=category)
    
    if status:
        assets = assets.filter(status=status)
    
    serializer = AssetListSerializer(assets[:20], many=True)
    return Response(serializer.data)