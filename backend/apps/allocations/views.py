from rest_framework import generics, filters, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.utils import timezone
from apps.core.permissions import IsAdminOrManagerOrReadOnly
from .models import Allocation
from .serializers import (
    AllocationListSerializer, AllocationDetailSerializer,
    AllocationCreateSerializer, AllocationReturnSerializer
)


class AllocationListCreateView(generics.ListCreateAPIView):
    queryset = Allocation.objects.select_related('asset', 'employee').all()
    permission_classes = [IsAdminOrManagerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['asset__name', 'asset__serial_number', 'employee__first_name', 'employee__last_name']
    filterset_fields = ['asset__category', 'employee', 'returned_at']
    ordering_fields = ['allocated_at', 'returned_at']
    ordering = ['-allocated_at']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AllocationCreateSerializer
        return AllocationListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter based on user role
        if user.role == 'employee':
            queryset = queryset.filter(employee=user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter == 'active':
            queryset = queryset.filter(returned_at__isnull=True)
        elif status_filter == 'returned':
            queryset = queryset.filter(returned_at__isnull=False)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AllocationRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Allocation.objects.select_related('asset', 'employee').all()
    permission_classes = [IsAdminOrManagerOrReadOnly]
    
    def get_serializer_class(self):
        if self.request.method == 'PATCH' and 'return' in self.request.path:
            return AllocationReturnSerializer
        return AllocationDetailSerializer


@api_view(['PATCH'])
def return_asset(request, pk):
    """Return an allocated asset"""
    try:
        allocation = Allocation.objects.get(pk=pk, returned_at__isnull=True)
    except Allocation.DoesNotExist:
        return Response({'error': 'Active allocation not found'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = AllocationReturnSerializer(allocation, data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(AllocationDetailSerializer(allocation).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def allocation_stats(request):
    """Get allocation statistics"""
    stats = {
        'total_allocations': Allocation.objects.count(),
        'active_allocations': Allocation.objects.filter(returned_at__isnull=True).count(),
        'returned_allocations': Allocation.objects.filter(returned_at__isnull=False).count(),
        'by_employee': list(Allocation.objects.filter(returned_at__isnull=True)
                          .values('employee__first_name', 'employee__last_name')
                          .annotate(count=Count('id'))
                          .order_by('-count')[:10]),
        'by_category': list(Allocation.objects.filter(returned_at__isnull=True)
                          .values('asset__category__name')
                          .annotate(count=Count('id'))
                          .order_by('-count')),
    }
    return Response(stats)


@api_view(['GET'])
def my_allocations(request):
    """Get current user's allocations"""
    allocations = Allocation.objects.filter(
        employee=request.user,
        returned_at__isnull=True
    ).select_related('asset')
    
    serializer = AllocationListSerializer(allocations, many=True)
    return Response(serializer.data)