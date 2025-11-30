"""
Tests de integración para el sistema de reservas.
Estas pruebas verifican el flujo completo desde la interfaz web hasta la base de datos.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.timezone import now, make_aware
from datetime import datetime, timedelta
from gestion_reservas.models import Reserva, Espacio
import json


class ReservaIntegrationTestCase(TestCase):
    """Test de integración completo del sistema de reservas"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.client = Client()
        
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Crear usuario administrador
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        # Autenticar el usuario normal
        self.client.login(username='testuser', password='testpass123')
    
    def test_flujo_completo_reserva(self):
        """Test del flujo completo: crear, modificar y eliminar reserva"""
        
        # 1. Crear una reserva
        fecha_futura = now() + timedelta(days=1)
        fecha_futura = fecha_futura.replace(minute=0, second=0, microsecond=0)
        
        data_crear = {
            'momento_inicio': fecha_futura.isoformat(),
            'momento_fin': (fecha_futura + timedelta(hours=1)).isoformat(),
            'espacio': 'Fútbol'
        }
        
        response = self.client.post(
            reverse('crear_reserva_api'),
            data=json.dumps(data_crear),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data_response = json.loads(response.content)
        reserva_id = data_response['id']
        
        # Verificar que la reserva se creó en la base de datos
        reserva = Reserva.objects.get(id=reserva_id)
        self.assertEqual(reserva.user_id, self.user)
        self.assertEqual(reserva.espacio, Espacio.FUTBOL)
        
        # 2. Modificar la reserva (cambiar hora)
        nueva_fecha = fecha_futura + timedelta(hours=2)
        data_modificar = {
            'momento_inicio': nueva_fecha.isoformat(),
            'momento_fin': (nueva_fecha + timedelta(hours=1)).isoformat()
        }
        
        response = self.client.put(
            reverse('modificar_reserva', kwargs={'reserva_id': reserva_id}),
            data=json.dumps(data_modificar),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar que la modificación se guardó
        reserva.refresh_from_db()
        self.assertEqual(reserva.momento_inicio.replace(tzinfo=None), 
                        nueva_fecha.replace(tzinfo=None))
        
        # 3. Verificar que aparece en "Mis Reservas"
        response = self.client.get(reverse('reservas'))
        self.assertEqual(response.status_code, 200)
        # Verificar que hay al menos una reserva mostrada
        self.assertContains(response, 'Fútbol')
        self.assertContains(response, 'reserva-card')
        
        # 4. Eliminar la reserva
        response = self.client.delete(
            reverse('eliminar_reserva', kwargs={'reserva_id': reserva_id})
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar que la reserva se eliminó de la base de datos
        self.assertFalse(Reserva.objects.filter(id=reserva_id).exists())
    
    def test_horarios_disponibles_api(self):
        """Test de la API de horarios disponibles"""
        
        # Crear una reserva existente
        fecha_futura = now() + timedelta(days=1)
        fecha_futura = fecha_futura.replace(minute=0, second=0, microsecond=0)
        
        Reserva.objects.create(
            user_id=self.user,
            momento_inicio=fecha_futura,
            momento_fin=fecha_futura + timedelta(hours=1),
            espacio=Espacio.FUTBOL,
            created_at=now()
        )
        
        # Consultar horarios disponibles
        data = {
            'espacio': 'Fútbol',
            'fecha': fecha_futura.strftime('%Y-%m-%d')
        }
        
        response = self.client.post(
            reverse('horarios_disponibles'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data_response = json.loads(response.content)
        
        # Verificar que el horario ocupado aparece en la respuesta
        hora_ocupada = fecha_futura.strftime('%H:%M')
        self.assertIn(hora_ocupada, data_response['horarios_ocupados'])
    
    def test_limite_tres_reservas(self):
        """Test del límite de 3 reservas activas por usuario"""
        
        # Crear 3 reservas
        for i in range(3):
            fecha_futura = now() + timedelta(days=i+1)
            fecha_futura = fecha_futura.replace(minute=0, second=0, microsecond=0)
            
            Reserva.objects.create(
                user_id=self.user,
                momento_inicio=fecha_futura,
                momento_fin=fecha_futura + timedelta(hours=1),
                espacio=Espacio.FUTBOL,
                created_at=now()
            )
        
        # Intentar crear una cuarta reserva
        fecha_futura = now() + timedelta(days=4)
        fecha_futura = fecha_futura.replace(minute=0, second=0, microsecond=0)
        
        data = {
            'momento_inicio': fecha_futura.isoformat(),
            'momento_fin': (fecha_futura + timedelta(hours=1)).isoformat(),
            'espacio': 'Baloncesto'
        }
        
        response = self.client.post(
            reverse('crear_reserva_api'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data_response = json.loads(response.content)
        self.assertIn('más de 3 reservas', data_response['error'])