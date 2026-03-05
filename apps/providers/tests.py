from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal
from rest_framework.test import APIClient
from rest_framework import status
from .models import Provider, Service


# ── helpers ──────────────────────────────────────────────────────────────────

def make_user(username='testuser', is_staff=False):
    return User.objects.create_user(
        username=username, password='pass',
        email=f'{username}@test.com', is_staff=is_staff,
    )


def make_provider(owner, email='biz@example.com'):
    return Provider.objects.create(
        name='Test Biz', email=email,
        phone='1234567890', business_type='hotel', owner=owner,
    )


PROVIDER_PAYLOAD = {
    'name': 'New Biz',
    'email': 'new@example.com',
    'phone': '0987654321',
    'business_type': 'hotel',
}


# ── Model tests ───────────────────────────────────────────────────────────────

class ProviderModelTests(TestCase):

    def test_provider_creation_with_valid_data(self):
        """Provider is created and saved correctly with valid data."""
        owner = make_user()
        provider = make_provider(owner)
        self.assertEqual(Provider.objects.count(), 1)
        self.assertEqual(provider.name, 'Test Biz')
        self.assertEqual(provider.business_type, 'hotel')
        self.assertFalse(provider.is_verified)
        self.assertEqual(provider.owner, owner)

    def test_provider_creation_fails_with_duplicate_email(self):
        """Two providers cannot share the same email (unique constraint)."""
        owner = make_user()
        make_provider(owner, email='unique@example.com')
        with self.assertRaises(IntegrityError):
            make_provider(owner, email='unique@example.com')


class ServiceModelTests(TestCase):

    def test_service_with_negative_price_is_rejected(self):
        """Service price must be >= 0.01; negative value fails validation."""
        owner = make_user()
        provider = make_provider(owner)
        service = Service(
            provider=provider, title='Bad Service',
            description='desc', price=Decimal('-10.00'), duration_hours=1,
        )
        with self.assertRaises(ValidationError):
            service.full_clean()


# ── API tests ─────────────────────────────────────────────────────────────────

class ProviderAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.owner = make_user('owner')
        self.admin = make_user('admin', is_staff=True)
        self.other = make_user('other')
        self.provider = make_provider(self.owner)

    # 1. List providers returns paginated results
    def test_list_providers_returns_paginated_results(self):
        response = self.client.get('/providers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # DRF pagination wraps results in 'results' key
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)

    # 2. Create provider with valid data returns 201
    def test_create_provider_valid_data_returns_201(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post('/providers/', PROVIDER_PAYLOAD, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Biz')

    # 3. Create provider with invalid data returns 400
    def test_create_provider_invalid_data_returns_400(self):
        self.client.force_authenticate(user=self.owner)
        # missing required fields: phone, business_type
        response = self.client.post('/providers/', {'name': 'Bad'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 10. Admin can delete a provider; non-admin cannot
    def test_admin_can_delete_provider(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f'/providers/{self.provider.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_non_admin_cannot_delete_provider(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.delete(f'/providers/{self.provider.pk}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

