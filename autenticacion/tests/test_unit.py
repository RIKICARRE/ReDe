from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth.models import User
from autenticacion.forms import UserLoginForm
from autenticacion.views import user_login, user_logout

# Tests para formularios
class UserLoginFormTestCase(TestCase):
    def setUp(self):
        User.objects.create_user(username='12345678A', password='password123')

    def test_valid_login_form(self):
        form = UserLoginForm(data={'dni': '12345678A', 'password': 'password123'})
        self.assertTrue(form.is_valid())

    def test_invalid_login_form(self):
        form = UserLoginForm(data={'dni': '', 'password': 'password123'})
        self.assertFalse(form.is_valid())

    def test_invalid_password(self):
        form = UserLoginForm(data={'dni': '12345678A', 'password': 'wrongpassword'})
        self.assertFalse(form.is_valid())


# class UserRegistrationFormTestCase(TestCase):
#     def test_valid_registration_form(self):
#         form = UserRegistrationForm(data={
#             'dni': '12345678A',
#             'password': 'password123',
#             'confirm_password': 'password123'
#         })
#         self.assertTrue(form.is_valid())

#     def test_passwords_do_not_match(self):
#         form = UserRegistrationForm(data={
#             'dni': '12345678A',
#             'password': 'password123',
#             'confirm_password': 'differentpassword'
#         })
#         self.assertFalse(form.is_valid())

    # def test_dni_already_registered(self):
    #     User.objects.create_user(username='12345678A', password='password123')
    #     form = UserRegistrationForm(data={
    #         'dni': '12345678A',
    #         'password': 'password123',
    #         'confirm_password': 'password123'
    #     })
    #     self.assertFalse(form.is_valid())

    # def test_invalid_dni_format(self):
    #     form = UserRegistrationForm(data={'dni': '12345', 'password': 'password123', 'confirm_password': 'password123'})
    #     self.assertFalse(form.is_valid())


# Tests para vistas
# class RegisterViewTestCase(TestCase):
#     def test_register_view_renders_correct_template(self):
#         response = self.client.get(reverse('register'))
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'autenticacion/register.html')

#     def test_register_creates_user_on_valid_data(self):
#         response = self.client.post(reverse('register'), data={
#             'dni': '12345678A',
#             'password': 'password123',
#             'confirm_password': 'password123'
#         })
#         self.assertEqual(User.objects.count(), 1)
#         self.assertRedirects(response, reverse('login'))

#     def test_register_shows_errors_on_invalid_data(self):
#         response = self.client.post(reverse('register'), data={
#             'dni': '',
#             'password': 'password123',
#             'confirm_password': 'password123'
#         })
#         self.assertEqual(User.objects.count(), 0)
#         self.assertContains(response, "Este campo es obligatorio.")

class LoginViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='12345678A', password='password123')

    def test_login_view_renders_correct_template(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'autenticacion/login.html')

    def test_login_authenticates_user(self):
        response = self.client.post(reverse('login'), data={
            'dni': '12345678A',
            'password': 'password123'
        })
        self.assertRedirects(response, reverse('home'))

    def test_login_shows_error_on_invalid_credentials(self):
        response = self.client.post(reverse('login'), data={
            'dni': '12345678A',
            'password': 'wrongpassword'
        })
        self.assertContains(response, "Credenciales incorrectas")

class LogoutViewTestCase(TestCase):
    def test_logout_redirects_to_login(self):
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))

# Tests para URLs
class URLResolutionTestCase(TestCase):
    # def test_register_url_resolves_to_correct_view(self):
    #     resolver = resolve(reverse('register'))
    #     self.assertEqual(resolver.func, register)

    def test_login_url_resolves_to_correct_view(self):
        resolver = resolve(reverse('login'))
        self.assertEqual(resolver.func, user_login)

    def test_logout_url_resolves_to_correct_view(self):
        resolver = resolve(reverse('logout'))
        self.assertEqual(resolver.func, user_logout)