from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.core.urls')),
    path('api/assets/', include('apps.assets.urls')),
    path('api/employees/', include('apps.employees.urls')),
    path('api/allocations/', include('apps.allocations.urls')),
    path('api/maintenance/', include('apps.maintenance.urls')),
    path('api/reports/', include('apps.reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = "Asset Management System"
admin.site.site_title = "Asset Management"
admin.site.index_title = "Administration"