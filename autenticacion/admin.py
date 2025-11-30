from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from gestion_reservas.models import Reserva

# Personalizar la gestión de usuarios
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined', 'get_reservas_count')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    
    def get_reservas_count(self, obj):
        return Reserva.objects.filter(user_id=obj).count()
    get_reservas_count.short_description = 'Núm. Reservas'
    
    # Añadir sección para ver reservas del usuario en la página de detalle
    def get_inline_instances(self, request, obj=None):
        inlines = super().get_inline_instances(request, obj)
        if obj:
            inlines.append(ReservaInline(self.model, self.admin_site))
        return inlines

class ReservaInline(admin.TabularInline):
    model = Reserva
    fk_name = 'user_id'
    extra = 0
    readonly_fields = ('espacio', 'momento_inicio', 'momento_fin', 'created_at')
    can_delete = True
    show_change_link = True

# Reemplazar el UserAdmin por defecto
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
