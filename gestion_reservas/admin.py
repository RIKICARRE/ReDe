from django.contrib import admin
from .models import Reserva
from django.contrib.auth.models import User

# Register your models here.
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'espacio', 'momento_inicio', 'momento_fin', 'created_at')
    list_filter = ('espacio', 'momento_inicio', 'created_at')
    search_fields = ('user_id__username', 'user_id__email', 'espacio')
    readonly_fields = ('created_at',)
    date_hierarchy = 'momento_inicio'
    ordering = ('-momento_inicio',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user_id')

admin.site.register(Reserva, ReservaAdmin)

# Personalizar el panel de administración
admin.site.site_header = "ReDe - Panel de Administración"
admin.site.site_title = "ReDe Admin"
admin.site.index_title = "Gestión del Sistema ReDe"
