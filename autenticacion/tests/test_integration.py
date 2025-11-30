from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

class AutenticacionIntegrationTestCase(TestCase):
    def test_register_login_logout_flow(self):
        response = self.client.post(reverse('register'), data={
            'dni': '12345678A',
            'password': 'password123',
            'confirm_password': 'password123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='12345678A').exists())

        response = self.client.post(reverse('login'), data={
            'dni': '12345678A',
            'password': 'password123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('_auth_user_id', self.client.session)

        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_invalid_register_shows_error(self):
        response = self.client.post(reverse('register'), data={
            'dni': '12345678A',
            'password': 'password123',
            'confirm_password': 'differentpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Las contraseñas no coinciden.")
        self.assertFalse(User.objects.filter(username='12345678A').exists())

    def test_login_with_invalid_credentials(self):
        response = self.client.post(reverse('login'), data={
            'dni': '12345678A',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Credenciales incorrectas")

    def test_register_with_existing_dni(self):
        User.objects.create_user(username='12345678A', password='password123')
        response = self.client.post(reverse('register'), data={
            'dni': '12345678A',
            'password': 'password123',
            'confirm_password': 'password123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Este DNI ya está registrado.")
