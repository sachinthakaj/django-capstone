from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Booking
from .serializers import BookingSerializer
from .permissions import IsBookingOwner


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer

    def get_permissions(self):
        if self.action in ['retrieve', 'cancel', 'update', 'partial_update']:
            return [permissions.IsAuthenticated(), IsBookingOwner()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Booking.objects.filter(created_by=self.request.user).order_by('id')

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user
        )

    @action(detail=True, methods=['patch'])
    def cancel(self, request, pk=None):
        """POST /api/bookings/{id}/cancel/ — Cancel a booking (owner only)"""
        booking = self.get_object()
        if not booking.status == 'pending':
            return Response({'detail': 'Booking cannot be cancelled.'}, status=400)
        booking.status = 'cancelled'
        booking.save()
        return Response(BookingSerializer(booking).data)
