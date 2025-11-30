from django.contrib import admin
from .models import Reserva, LineaReserva, Fianza
# Register your models here.
class ReservaAdmin(admin.ModelAdmin):
    readonly_fields=('created_at',)
admin.site.register(Reserva, ReservaAdmin)
admin.site.register(LineaReserva)
admin.site.register(Fianza)
