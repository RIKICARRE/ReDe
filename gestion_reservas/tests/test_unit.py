import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.timezone import make_aware
from datetime import datetime
from gestion_reservas.models import  Reserva

class ReservaViewTestCase(TestCase):
    def set_up(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')

    def test_crear_reserva_view(self):
        self.client.login(username='testuser', password='12345')
        data = {
            'momento_inicio': '2024-01-01T14:00:00',
            'momento_fin': '2024-01-01T15:00:00',
            'espacio': 'Baloncesto'
        }
        response = self.client.post(reverse('crear_reserva_view'), data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Reserva.objects.filter(user_id=self.user).exists())
        reserva = Reserva.objects.get(user_id=self.user)
        self.assertEqual(reserva.espacio, self.espacio)
        self.assertEqual(reserva.momento_inicio, make_aware(datetime(2024, 1, 1, 14, 0)))
        self.assertEqual(reserva.momento_fin, make_aware(datetime(2024, 1, 1, 15, 0)))

    def test_modificar_reserva_view_status_code(self):
        response = self.client.put(self.url, data=json.dumps({
        'momento_inicio': '2024-01-01T16:00:00',
        'momento_fin': '2024-01-01T17:00:00',
        'espacio': 'Baloncesto'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_modificar_reserva_view_changes(self):
        response = self.client.put(self.url, data=json.dumps({
            'momento_inicio': '2024-01-01T16:00:00',
            'momento_fin': '2024-01-01T17:00:00',
            'espacio': 'Baloncesto'
        }), content_type='application/json')
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.momento_inicio, make_aware(datetime(2024, 1, 1, 16, 0)))
        self.assertEqual(self.reserva.momento_fin, make_aware(datetime(2024, 1, 1, 17, 0)))

    def test_modificar_reserva_view_invalid_data(self):
        response = self.client.put(self.url, data=json.dumps({
            'momento_inicio': '2023-01-01T16:00:00',
            'momento_fin': '2023-01-01T17:00:00',
            'espacio': 'Baloncesto'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('La reserva tiene que ser en el futuro', response.json()['error'])