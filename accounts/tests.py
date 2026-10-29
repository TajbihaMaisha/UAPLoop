from django.test import TestCase
from django.urls import reverse

from .models import User


class RegisterTest(TestCase):
    def setUp(self):
        self.student = User.objects.create(full_name='Rahim Khan', university_id='21101001', phone='01700000001', email='rahim@example.com')

    def register(self, phone='01700000001'):
        return self.client.post(reverse('register'), {
            'university_id': '21101001', 'phone': phone, 'full_name': 'rahim khan',
            'email': 'rahim@example.com', 'password': 'strongpass99', 'confirm_password': 'strongpass99',
        })

    def test_register_needs_matching_record(self):
        self.assertEqual(self.register(phone='01700000009').status_code, 200)
        self.student.refresh_from_db()
        self.assertIsNone(self.student.registered_at)

    def test_register_once(self):
        self.assertEqual(self.register().status_code, 302)
        self.assertContains(self.register(), 'already registered')


class ErrorPageTest(TestCase):
    def test_login_required_shows_401_with_next(self):
        response = self.client.get('/new/', follow=True)
        self.assertEqual(response.status_code, 401)
        self.assertContains(response, 'Login required', status_code=401)
        self.assertContains(response, 'next=/new/', status_code=401)

    def test_missing_page_shows_custom_404(self):
        response = self.client.get('/no-such-page/')
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'Page not found', status_code=404)

    def test_login_goes_back_to_next(self):
        user = User(email='a@example.com', full_name='A')
        user.set_password('pass12345')
        user.save()
        response = self.client.post('/login/?next=/new/', {'username': 'a@example.com', 'password': 'pass12345'})
        self.assertRedirects(response, '/new/')
        response = self.client.post('/login/?next=http://evil.com/', {'username': 'a@example.com', 'password': 'pass12345'})
        self.assertRedirects(response, '/')
