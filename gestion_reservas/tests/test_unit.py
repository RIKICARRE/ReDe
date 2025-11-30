import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.timezone import make_aware, now
from datetime import datetime, timedelta
from gestion_reservas.models import Reserva, Espacio


class CrearReservaViewTestCase(TestCase):
    """Tests unitarios para crear reservas"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        
        # Fecha futura para las pruebas
        self.fecha_futura = now() + timedelta(days=1)
        self.fecha_futura = self.fecha_futura.replace(hour=14, minute=0, second=0, microsecond=0)

    def test_crear_reserva_exitosa(self):
        """Test crear reserva con datos válidos"""
        data = {
            'espacio': 'Baloncesto',
            'momento_inicio': self.fecha_futura.isoformat(),
            'momento_fin': (self.fecha_futura + timedelta(hours=1)).isoformat()
        }
        response = self.client.post(
            reverse('crear_reserva_api'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Reserva.objects.filter(user_id=self.user).exists())
        
        reserva = Reserva.objects.get(user_id=self.user)
        self.assertEqual(reserva.espacio, 'Baloncesto')
        self.assertEqual(reserva.momento_inicio.replace(microsecond=0), self.fecha_futura)

    def test_crear_reserva_fecha_pasada(self):
        """Test crear reserva con fecha en el pasado"""
        fecha_pasada = now() - timedelta(days=1)
        data = {
            'espacio': 'Fútbol',
            'momento_inicio': fecha_pasada.isoformat(),
            'momento_fin': (fecha_pasada + timedelta(hours=1)).isoformat()
        }
        response = self.client.post(
            reverse('crear_reserva_api'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('futuro', response_data['error'])

    def test_crear_reserva_duracion_incorrecta(self):
        """Test crear reserva que no dura exactamente 1 hora"""
        data = {
            'espacio': 'Padel',
            'momento_inicio': self.fecha_futura.isoformat(),
            'momento_fin': (self.fecha_futura + timedelta(hours=2)).isoformat()
        }
        response = self.client.post(
            reverse('crear_reserva_api'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('una hora', response_data['error'])

    def test_crear_reserva_limite_tres_reservas(self):
        """Test que no se pueden crear más de 3 reservas activas"""
        # Crear 3 reservas primero
        for i in range(3):
            fecha = self.fecha_futura + timedelta(hours=i*2)
            Reserva.objects.create(
                user_id=self.user,
                espacio='Baloncesto',
                momento_inicio=fecha,
                momento_fin=fecha + timedelta(hours=1)
            )
        
        # Intentar crear la cuarta
        data = {
            'espacio': 'Fútbol',
            'momento_inicio': (self.fecha_futura + timedelta(hours=8)).isoformat(),
            'momento_fin': (self.fecha_futura + timedelta(hours=9)).isoformat()
        }
        response = self.client.post(
            reverse('crear_reserva_api'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('3 reservas', response_data['error'])

    def test_crear_reserva_conflicto_horario(self):
        """Test crear reserva en horario ya ocupado"""
        # Crear primera reserva
        Reserva.objects.create(
            user_id=self.user,
            espacio='Baloncesto',
            momento_inicio=self.fecha_futura,
            momento_fin=self.fecha_futura + timedelta(hours=1)
        )
        
        # Intentar crear segunda reserva en el mismo horario y espacio
        data = {
            'espacio': 'Baloncesto',
            'momento_inicio': self.fecha_futura.isoformat(),
            'momento_fin': (self.fecha_futura + timedelta(hours=1)).isoformat()
        }
        response = self.client.post(
            reverse('crear_reserva_api'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('Ya existe', response_data['error'])

    def test_crear_reserva_usuario_no_autenticado(self):
        """Test crear reserva sin estar autenticado"""
        self.client.logout()
        
        data = {
            'espacio': 'Padel',
            'momento_inicio': self.fecha_futura.isoformat(),
            'momento_fin': (self.fecha_futura + timedelta(hours=1)).isoformat()
        }
        response = self.client.post(
            reverse('crear_reserva_api'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect to login


class ModificarReservaViewTestCase(TestCase):
    """Tests unitarios para modificar reservas"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        
        # Crear reserva para modificar
        self.fecha_original = now() + timedelta(days=1)
        self.fecha_original = self.fecha_original.replace(hour=14, minute=0, second=0, microsecond=0)
        
        self.reserva = Reserva.objects.create(
            user_id=self.user,
            espacio='Baloncesto',
            momento_inicio=self.fecha_original,
            momento_fin=self.fecha_original + timedelta(hours=1)
        )

    def test_modificar_reserva_hora_exitosa(self):
        """Test modificar solo la hora de una reserva"""
        nueva_fecha = self.fecha_original.replace(hour=16)
        data = {
            'momento_inicio': nueva_fecha.isoformat(),
            'momento_fin': (nueva_fecha + timedelta(hours=1)).isoformat()
        }
        
        response = self.client.put(
            reverse('modificar_reserva', kwargs={'reserva_id': self.reserva.id}),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.momento_inicio.replace(microsecond=0), nueva_fecha)
        self.assertEqual(self.reserva.espacio, 'Baloncesto')  # El espacio no debe cambiar

    def test_modificar_reserva_espacio_ignorado(self):
        """Test que el cambio de espacio se ignora en modificaciones"""
        nueva_fecha = self.fecha_original.replace(hour=16)
        data = {
            'espacio': 'Fútbol',  # Esto debe ser ignorado
            'momento_inicio': nueva_fecha.isoformat(),
            'momento_fin': (nueva_fecha + timedelta(hours=1)).isoformat()
        }
        
        response = self.client.put(
            reverse('modificar_reserva', kwargs={'reserva_id': self.reserva.id}),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.espacio, 'Baloncesto')  # No debe cambiar

    def test_modificar_reserva_fecha_pasada(self):
        """Test modificar reserva a fecha pasada"""
        fecha_pasada = now() - timedelta(days=1)
        data = {
            'momento_inicio': fecha_pasada.isoformat(),
            'momento_fin': (fecha_pasada + timedelta(hours=1)).isoformat()
        }
        
        response = self.client.put(
            reverse('modificar_reserva', kwargs={'reserva_id': self.reserva.id}),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('futuro', response_data['error'])

    def test_modificar_reserva_no_existente(self):
        """Test modificar reserva que no existe"""
        data = {
            'momento_inicio': self.fecha_original.isoformat(),
            'momento_fin': (self.fecha_original + timedelta(hours=1)).isoformat()
        }
        
        response = self.client.put(
            reverse('modificar_reserva', kwargs={'reserva_id': 9999}),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)

    def test_modificar_reserva_otro_usuario(self):
        """Test modificar reserva de otro usuario"""
        otro_user = User.objects.create_user(username='otrouser', password='testpass123')
        reserva_otro = Reserva.objects.create(
            user_id=otro_user,
            espacio='Fútbol',
            momento_inicio=self.fecha_original + timedelta(hours=2),
            momento_fin=self.fecha_original + timedelta(hours=3)
        )
        
        data = {
            'momento_inicio': self.fecha_original.isoformat(),
            'momento_fin': (self.fecha_original + timedelta(hours=1)).isoformat()
        }
        
        response = self.client.put(
            reverse('modificar_reserva', kwargs={'reserva_id': reserva_otro.id}),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)


class EliminarReservaViewTestCase(TestCase):
    """Tests unitarios para eliminar/cancelar reservas"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        
        # Crear reserva para eliminar
        fecha_futura = now() + timedelta(days=1)
        fecha_futura = fecha_futura.replace(hour=14, minute=0, second=0, microsecond=0)
        
        self.reserva = Reserva.objects.create(
            user_id=self.user,
            espacio='Baloncesto',
            momento_inicio=fecha_futura,
            momento_fin=fecha_futura + timedelta(hours=1)
        )

    def test_eliminar_reserva_exitosa(self):
        """Test eliminar reserva propia exitosamente"""
        response = self.client.delete(
            reverse('eliminar_reserva', kwargs={'reserva_id': self.reserva.id})
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        
        # Verificar que la reserva fue eliminada
        self.assertFalse(Reserva.objects.filter(id=self.reserva.id).exists())

    def test_eliminar_reserva_no_existente(self):
        """Test eliminar reserva que no existe"""
        response = self.client.delete(
            reverse('eliminar_reserva', kwargs={'reserva_id': 9999})
        )
        
        self.assertEqual(response.status_code, 404)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('no encontrada', response_data['error'])

    def test_eliminar_reserva_otro_usuario(self):
        """Test eliminar reserva de otro usuario"""
        otro_user = User.objects.create_user(username='otrouser', password='testpass123')
        reserva_otro = Reserva.objects.create(
            user_id=otro_user,
            espacio='Fútbol',
            momento_inicio=now() + timedelta(days=1),
            momento_fin=now() + timedelta(days=1, hours=1)
        )
        
        response = self.client.delete(
            reverse('eliminar_reserva', kwargs={'reserva_id': reserva_otro.id})
        )
        
        self.assertEqual(response.status_code, 404)
        
        # Verificar que la reserva del otro usuario no fue eliminada
        self.assertTrue(Reserva.objects.filter(id=reserva_otro.id).exists())

    def test_eliminar_reserva_usuario_no_autenticado(self):
        """Test eliminar reserva sin estar autenticado"""
        self.client.logout()
        
        response = self.client.delete(
            reverse('eliminar_reserva', kwargs={'reserva_id': self.reserva.id})
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect to login


class HorariosDisponiblesViewTestCase(TestCase):
    """Tests unitarios para obtener horarios disponibles"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')

    def test_horarios_disponibles_exitoso(self):
        """Test obtener horarios disponibles"""
        fecha = (now() + timedelta(days=1)).date()
        data = {
            'espacio': 'Baloncesto',
            'fecha': fecha.isoformat()
        }
        
        response = self.client.post(
            reverse('horarios_disponibles'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('horarios_ocupados', response_data)
        self.assertIsInstance(response_data['horarios_ocupados'], list)

    def test_horarios_disponibles_con_reserva_existente(self):
        """Test horarios ocupados con reserva existente"""
        fecha = now() + timedelta(days=1)
        fecha = fecha.replace(hour=14, minute=0, second=0, microsecond=0)
        
        # Crear reserva
        Reserva.objects.create(
            user_id=self.user,
            espacio='Baloncesto',
            momento_inicio=fecha,
            momento_fin=fecha + timedelta(hours=1)
        )
        
        data = {
            'espacio': 'Baloncesto',
            'fecha': fecha.date().isoformat()
        }
        
        response = self.client.post(
            reverse('horarios_disponibles'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('14:00', response_data['horarios_ocupados'])

    def test_horarios_disponibles_datos_faltantes(self):
        """Test horarios disponibles sin datos requeridos"""
        data = {'espacio': 'Baloncesto'}  # Falta fecha
        
        response = self.client.post(
            reverse('horarios_disponibles'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('error', response_data)