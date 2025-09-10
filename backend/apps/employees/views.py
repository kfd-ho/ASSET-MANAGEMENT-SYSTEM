from rest_framework import generics, filters, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from apps.core.permissions import IsAdminOrManagerOrReadOnly, IsAdminOrManager
from .models import Department, Employee
from .serializers import (
    DepartmentSerializer, EmployeeListSerializer, EmployeeDetailSerializer,
    EmployeeCreateSerializer, EmployeeUpdateSerializer
)


class DepartmentListCreateView(generics.ListCreateAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class DepartmentRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class EmployeeListCreateView(generics.ListCreateAPIView):
    queryset = Employee.objects.select_related('user', 'department').all()
    permission_classes = [IsAdminOrManagerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['employee_id', 'user__first_name', 'user__last_name', 'user__email']
    filterset_fields = ['department', 'employment_type', 'is_active']
    ordering_fields = ['employee_id', 'join_date', 'user__first_name']
    ordering = ['employee_id']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EmployeeCreateSerializer
        return EmployeeListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter based on user role
        if user.role == 'manager':
            # Managers can see employees in their department or subordinates
            queryset = queryset.filter(
                Q(department=user.employee.department) |
                Q(reporting_manager=user)
            )
        elif user.role == 'employee':
            # Employees can only see themselves
            queryset = queryset.filter(user=user)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class EmployeeRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Employee.objects.select_related('user', 'department').all()
    permission_classes = [IsAdminOrManagerOrReadOnly]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return EmployeeUpdateSerializer
        return EmployeeDetailSerializer
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


@api_view(['GET'])
def employee_stats(request):
    """Get employee statistics"""
    stats = {
        'total_employees': Employee.objects.filter(is_active=True).count(),
        'by_department': list(Employee.objects.values('department__name').annotate(
            count=Count('id')
        ).values('department__name', 'count')),
        'by_employment_type': dict(Employee.objects.values('employment_type').annotate(
            count=Count('id')
        ).values_list('employment_type', 'count')),
        'active_employees': Employee.objects.filter(is_active=True).count(),
        'inactive_employees': Employee.objects.filter(is_active=False).count(),
    }
    return Response(stats)


@api_view(['GET'])
def department_hierarchy(request):
    """Get department hierarchy"""
    def build_tree(parent=None):
        departments = Department.objects.filter(parent=parent)
        return [{
            'id': dept.id,
            'name': dept.name,
            'description': dept.description,
            'manager': dept.manager.get_full_name() if dept.manager else None,
            'employee_count': Employee.objects.filter(department=dept, is_active=True).count(),
            'children': build_tree(dept)
        } for dept in departments]
    
    hierarchy = build_tree()
    return Response(hierarchy)


@api_view(['GET'])
def search_employees(request):
    """Search employees"""
    query = request.GET.get('q', '')
    department = request.GET.get('department', '')
    
    employees = Employee.objects.select_related('user', 'department').filter(is_active=True)
    
    if query:
        employees = employees.filter(
            Q(employee_id__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__email__icontains=query)
        )
    
    if department:
        employees = employees.filter(department_id=department)
    
    # Apply role-based filtering
    user = request.user
    if user.role == 'manager':
        employees = employees.filter(
            Q(department=user.employee.department) |
            Q(reporting_manager=user)
        )
    elif user.role == 'employee':
        employees = employees.filter(user=user)
    
    serializer = EmployeeListSerializer(employees[:20], many=True)
    return Response(serializer.data)