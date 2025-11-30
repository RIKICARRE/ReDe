# views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Reserva, Espacio  # Fianza eliminada del flujo
from django.http import JsonResponse
from django.utils.timezone import make_aware, is_aware
from datetime import datetime, timedelta
from django.utils.timezone import now
from django.contrib import messages
import json

def user_only(view_func):
    """Decorador que redirige a admin si el usuario es superuser"""
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_superuser:
            messages.info(request, 'Los administradores deben gestionar las reservas desde el panel de administración.')
            return redirect('/admin-info/')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
def admin_info_view(request):
    """Página informativa para administradores"""
    if not request.user.is_superuser:
        return redirect('/')
    return render(request, 'admin_info.html')

@login_required
@user_only
def reservas_view(request):
    """Página 'Mis reservas' SOLO lista y permite abrir panel de edición (sin crear)."""
    reservas = Reserva.objects.filter(user_id=request.user, momento_inicio__gte=now()).order_by('momento_inicio')
    return render(request, 'mis_reservas.html', {'reservas': reservas})

@login_required
@user_only
def crear_reserva_page(request):
    deportes = [
        {"code": "Fútbol", "titulo": "Fútbol", "desc": "Campo de fútbol"},
        {"code": "Baloncesto", "titulo": "Baloncesto", "desc": "Cancha de baloncesto"},
        {"code": "Padel", "titulo": "Pádel", "desc": "Pista de pádel"},
        {"code": "Piscina1", "titulo": "Piscina 1", "desc": "Carril 1"},
        {"code": "Piscina2", "titulo": "Piscina 2", "desc": "Carril 2"},
    ]
    return render(request, 'crear_reserva.html', {"deportes": deportes})

@login_required
@user_only
def historial_reservas_view(request):
    # Obtener reservas pasadas (donde momento_fin es menor que la fecha actual)
    reservas_pasadas = Reserva.objects.filter(user_id=request.user, momento_fin__lt=now())
    return render(request, 'historial_reservas.html', {'reservas': reservas_pasadas})

@login_required
@user_only
def crear_reserva_view(request):
    """Crear nueva reserva (sin lógica de fianza)."""
    if request.user.is_superuser:
        return JsonResponse({"error": "Los administradores no pueden crear reservas desde esta interfaz"}, status=403)
    
    data = json.loads(request.body)
    momento_inicio = data.get('momento_inicio')
    momento_fin = data.get('momento_fin')
    espacio_str = data.get('espacio')

    espacio = evaluate(espacio_str)
    
    # Manejar datetime aware o naive
    momento_inicio_dt = datetime.fromisoformat(momento_inicio)
    if not is_aware(momento_inicio_dt):
        momento_inicio_aware = make_aware(momento_inicio_dt)
    else:
        momento_inicio_aware = momento_inicio_dt
    
    momento_fin_dt = datetime.fromisoformat(momento_fin)
    if not is_aware(momento_fin_dt):
        momento_fin_aware = make_aware(momento_fin_dt)
    else:
        momento_fin_aware = momento_fin_dt

    user = request.user
    resultado_validacion = validate_post(user, momento_inicio_aware, momento_fin_aware, espacio)
    if resultado_validacion is not None:
        return resultado_validacion

    reserva = Reserva.objects.create(
        user_id=user,
        momento_inicio=momento_inicio_aware,
        momento_fin=momento_fin_aware,
        espacio=espacio,
        created_at=now()
    )

    return JsonResponse({
        "id": reserva.id,
        "momento_inicio": reserva.momento_inicio,
        "momento_fin": reserva.momento_fin,
        "espacio": reserva.espacio,
        "created_at": reserva.created_at
    }, status=201)

@login_required
@user_only
def modificar_reserva_view(request, reserva_id):
    """Modificar SOLO la hora de una reserva existente. El deporte no se permite cambiar."""
    if request.user.is_superuser:
        return JsonResponse({"error": "Los administradores no pueden modificar reservas desde esta interfaz"}, status=403)
    
    user = request.user
    try:
        reserva = Reserva.objects.get(id=reserva_id, user_id=user)
    except Reserva.DoesNotExist:
        return JsonResponse({"error": "Reserva no encontrada"}, status=404)
        
    data = json.loads(request.body)

    # Ignorar cambios de deporte si vienen en el payload
    if 'espacio' in data:
        data.pop('espacio')

    momento_inicio = data.get('momento_inicio')
    momento_fin = data.get('momento_fin')

    if momento_inicio:
        momento_inicio_dt = datetime.fromisoformat(momento_inicio)
        if not is_aware(momento_inicio_dt):
            reserva.momento_inicio = make_aware(momento_inicio_dt)
        else:
            reserva.momento_inicio = momento_inicio_dt
            
    if momento_fin:
        momento_fin_dt = datetime.fromisoformat(momento_fin)
        if not is_aware(momento_fin_dt):
            reserva.momento_fin = make_aware(momento_fin_dt)
        else:
            reserva.momento_fin = momento_fin_dt

    resultado_validacion = validate_put(user, reserva, data)
    if resultado_validacion is not None:
        return resultado_validacion
    reserva.save()

    return JsonResponse({
        "id": reserva.id,
        "momento_inicio": reserva.momento_inicio,
        "momento_fin": reserva.momento_fin,
        "espacio": reserva.espacio
    })

@login_required
@user_only
def eliminar_reserva_view(request, reserva_id):
    if request.user.is_superuser:
        return JsonResponse({"error": "Los administradores no pueden eliminar reservas desde esta interfaz"}, status=403)
    
    user = request.user
    try:
        reserva = Reserva.objects.get(id=reserva_id, user_id=user)
        reserva.delete()
        return JsonResponse({"success": True}, status=200)
    except Reserva.DoesNotExist:
        return JsonResponse({"error": "Reserva no encontrada"}, status=404)

def evaluate(pista_str):
    match pista_str:
        case 'Baloncesto':
            return Espacio.BALONCESTO
        case 'Fútbol':
            return Espacio.FUTBOL
        case 'Padel':
            return Espacio.PADEL
        case 'Piscina1':
            return Espacio.PISCINA1
        case 'Piscina2':
            return Espacio.PISCINA2

def validate_post(user, momento_inicio, momento_fin, espacio):
    if momento_fin - momento_inicio != timedelta(hours=1):
        return JsonResponse({"error": "La reserva debe durar una hora"})
    if Reserva.objects.filter(user_id=user, momento_inicio__gte=now()).count() >= 3:
        return JsonResponse({"error": "No puedes tener más de 3 reservas activas"})
    if Reserva.objects.filter(espacio=espacio, momento_inicio=momento_inicio, momento_fin=momento_fin).exists():
        return JsonResponse({"error": "Ya existe una reserva en ese momento"})
    if momento_inicio < now() or momento_fin < now():
        return JsonResponse({"error": "La reserva tiene que ser en el futuro"})
    if momento_inicio.minute != 0 or momento_fin.minute != 0:
        return JsonResponse({"error": "La reserva tiene que empezar y terminar en punto"})
    return None

def validate_put(user, reserva, data):
    # Validaciones de tiempo
    if data.get('momento_inicio'):
        momento_inicio_dt = datetime.fromisoformat(data.get('momento_inicio'))
        if not is_aware(momento_inicio_dt):
            momento_inicio = make_aware(momento_inicio_dt)
        else:
            momento_inicio = momento_inicio_dt
            
        if reserva.momento_fin - momento_inicio != timedelta(hours=1):
            return JsonResponse({"error": "La reserva debe durar una hora"})
        if momento_inicio < now():
            return JsonResponse({"error": "La reserva tiene que ser en el futuro"})
        if momento_inicio.minute != 0:
            return JsonResponse({"error": "La reserva tiene que empezar en punto"})

    if data.get('momento_fin'):
        momento_fin_dt = datetime.fromisoformat(data.get('momento_fin'))
        if not is_aware(momento_fin_dt):
            momento_fin = make_aware(momento_fin_dt)
        else:
            momento_fin = momento_fin_dt
            
        if momento_fin - reserva.momento_inicio != timedelta(hours=1):
            return JsonResponse({"error": "La reserva debe durar una hora"})
        if momento_fin < now():
            return JsonResponse({"error": "La reserva tiene que ser en el futuro"})
        if momento_fin.minute != 0:
            return JsonResponse({"error": "La reserva tiene que terminar en punto"})

    # Verificar límite de reservas activas (sin contar la reserva actual)
    reservas_activas = Reserva.objects.filter(user_id=user, momento_inicio__gte=now()).exclude(id=reserva.id).count()
    if reservas_activas >= 3:
        return JsonResponse({"error": "No puedes tener más de 3 reservas activas"})

    # Verificar conflictos de horario (excluyendo la reserva actual)
    # Espacio no modificable aquí
    espacio = reserva.espacio
    
    if data.get('momento_inicio'):
        momento_inicio_dt = datetime.fromisoformat(data.get('momento_inicio'))
        if not is_aware(momento_inicio_dt):
            momento_inicio = make_aware(momento_inicio_dt)
        else:
            momento_inicio = momento_inicio_dt
    else:
        momento_inicio = reserva.momento_inicio
        
    if data.get('momento_fin'):
        momento_fin_dt = datetime.fromisoformat(data.get('momento_fin'))
        if not is_aware(momento_fin_dt):
            momento_fin = make_aware(momento_fin_dt)
        else:
            momento_fin = momento_fin_dt
    else:
        momento_fin = reserva.momento_fin
    
    if Reserva.objects.filter(
        espacio=espacio, 
        momento_inicio=momento_inicio, 
        momento_fin=momento_fin
    ).exclude(id=reserva.id).exists():
        return JsonResponse({"error": "Ya existe una reserva en ese momento"})
    
    return None

@login_required
@user_only
def horarios_disponibles_view(request):
    """Vista para obtener los horarios ocupados en una fecha específica para un deporte"""
    if request.user.is_superuser:
        return JsonResponse({"error": "Los administradores no pueden acceder a esta funcionalidad"}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({"error": "Método no permitido"}, status=405)
    
    try:
        data = json.loads(request.body)
        espacio_str = data.get('espacio')
        fecha_str = data.get('fecha')
        reserva_id = data.get('reserva_id')  # Para excluir en caso de edición
        
        if not espacio_str or not fecha_str:
            return JsonResponse({"error": "Faltan datos requeridos"}, status=400)
        
        espacio = evaluate(espacio_str)
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        
        # Obtener reservas para esa fecha y espacio
        reservas_query = Reserva.objects.filter(
            espacio=espacio,
            momento_inicio__date=fecha
        )
        
        # Excluir la reserva actual si estamos editando
        if reserva_id:
            reservas_query = reservas_query.exclude(id=reserva_id)
        
        horarios_ocupados = []
        for reserva in reservas_query:
            hora = reserva.momento_inicio.strftime('%H:%M')
            horarios_ocupados.append(hora)
        
        return JsonResponse({
            "horarios_ocupados": horarios_ocupados
        })
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
