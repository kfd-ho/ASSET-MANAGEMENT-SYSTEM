from django.urls import path
from . import views

urlpatterns = [
    path('departments/', views.DepartmentListCreateView.as_view(), name='department-list-create'),
    path('departments/<int:pk>/', views.DepartmentRetrieveUpdateDestroyView.as_view(), name='department-detail'),
    path('departments/hierarchy/', views.department_hierarchy, name='department-hierarchy'),
    
    path('', views.EmployeeListCreateView.as_view(), name='employee-list-create'),
    path('<int:pk>/', views.EmployeeRetrieveUpdateDestroyView.as_view(), name='employee-detail'),
    
    path('stats/', views.employee_stats, name='employee-stats'),
    path('search/', views.search_employees, name='employee-search'),
]