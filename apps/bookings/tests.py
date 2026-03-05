from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from apps.providers.models import Provider, Service
from .models import Booking


# ── helpers ──────────────────────────────────────────────────────────────────

def make_user(username='bookinguser'):
    return User.objects.create_user(
        username=username, password='pass', email=f'{username}@test.com'
    )


def make_provider(owner):
    return Provider.objects.create(
        name='Test Biz', email='biz@example.com',
        phone='1234567890', business_type='hotel', owner=owner,
    )


def make_service(provider, price=Decimal('100.00')):
    return Service.objects.create(
        provider=provider, title='Test Service',
        description='desc', price=price, duration_hours=2,
    )


def make_booking(service, user, status='pending', days_ahead=5):
    return Booking.objects.create(
        service=service,
        customer_name=user.username,
        customer_email=user.email,
        booking_date=timezone.now().date() + timedelta(days=days_ahead),
        number_of_guests=2,
        created_by=user,
        status=status,
    )


BOOKING_PAYLOAD = {
    'customer_name': 'Alice',
    'customer_email': 'alice@example.com',
    'booking_date': (timezone.now().date() + timedelta(days=7)).isoformat(),
    'number_of_guests': 2,
}


# ── Model tests ───────────────────────────────────────────────────────────────

class BookingModelTests(TestCase):

    def setUp(self):
        self.user = make_user()
        self.provider = make_provider(self.user)
        self.service = make_service(self.provider)

    def test_booking_with_past_date_is_rejected(self):
        """Booking date must be in the future; past date raises ValidationError."""
        booking = Booking(
            service=self.service,
            customer_name='Alice',
            customer_email='alice@example.com',
            booking_date=timezone.now().date() - timedelta(days=1),
            number_of_guests=2,
            created_by=self.user,
        )
        with self.assertRaises(ValidationError):
            booking.full_clean()

    def test_total_price_is_calculated_correctly(self):
        """total_price == service.price * number_of_guests, set automatically on save."""
        booking = Booking.objects.create(
            service=self.service,
            customer_name='Bob',
            customer_email='bob@example.com',
            booking_date=timezone.now().date() + timedelta(days=5),
            number_of_guests=3,
            created_by=self.user,
        )
        self.assertEqual(booking.total_price, Decimal('300.00'))


# ── API tests ─────────────────────────────────────────────────────────────────

class BookingAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = make_user('user1')
        self.other = make_user('user2')
        provider_owner = make_user('owner')
        self.provider = make_provider(provider_owner)
        self.service = make_service(self.provider)

    # 4. Unauthenticated user cannot create a booking (401)
    def test_unauthenticated_cannot_create_booking(self):
        response = self.client.post(
            f'/services/{self.service.pk}/book/', BOOKING_PAYLOAD, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # 5. Authenticated user can create a booking (201)
    def test_authenticated_user_can_create_booking(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            f'/services/{self.service.pk}/book/', BOOKING_PAYLOAD, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Booking.objects.count(), 1)
        self.assertEqual(Booking.objects.first().created_by, self.user)

    # 6. User can only see their own bookings
    def test_user_can_only_see_own_bookings(self):
        make_booking(self.service, self.user)
        make_booking(self.service, self.other)
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/bookings/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [b['id'] for b in response.data['results']]
        # Only the booking owned by self.user should appear
        self.assertEqual(len(ids), 1)
        self.assertEqual(Booking.objects.get(pk=ids[0]).created_by, self.user)

    # 7. User cannot access another user's booking (404, not 403)
    def test_user_cannot_access_other_users_booking(self):
        other_booking = make_booking(self.service, self.other)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/bookings/{other_booking.pk}/')
        # get_queryset filters by created_by, so the object is not found → 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # 8. Cancel booking works for pending bookings
    def test_cancel_pending_booking(self):
        booking = make_booking(self.service, self.user, status='pending')
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f'/bookings/{booking.pk}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')

    # 9. Cancel booking fails for already confirmed bookings
    def test_cancel_confirmed_booking_fails(self):
        booking = make_booking(self.service, self.user, status='confirmed')
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f'/bookings/{booking.pk}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'confirmed')  # unchanged

    # 11. Cannot book an inactive service (404 — inactive services excluded from queryset)
    def test_cannot_book_inactive_service(self):
        inactive_service = Service.objects.create(
            provider=self.provider,
            title='Inactive Service',
            description='desc',
            price=Decimal('50.00'),
            duration_hours=1,
            is_active=False,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            f'/services/{inactive_service.pk}/book/', BOOKING_PAYLOAD, format='json'
        )
        # ServiceViewSet queryset filters is_active=True, so inactive services
        # are not found at all — returns 404 rather than 400
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

