from rest_framework import serializers
from .models import Booking
from django.utils import timezone


class BookingSerializer(serializers.ModelSerializer):
    service = serializers.PrimaryKeyRelatedField(read_only=True)
    service_title = serializers.CharField(source="service.title", read_only=True)
    provider_name = serializers.CharField(
        source="service.provider.name", read_only=True
    )

    class Meta:
        model = Booking
        fields = [
            "id",
            "service",
            "service_title",
            "provider_name",
            "customer_name",
            "customer_email",
            "booking_date",
            "number_of_guests",
            "total_price",
            "status",
            "notes",
            "created_by",
        ]
        read_only_fields = ["total_price", "status", "created_by"]

    def validate(self, data):
        booking_date = data.get("booking_date")
        if booking_date and booking_date <= timezone.now().date():
            raise serializers.ValidationError(
                {"booking_date": "Booking date must be in the future."}
            )

        service = self.context.get("service")

        if service and not getattr(service, "is_active", False):
            raise serializers.ValidationError("Cannot book an inactive service.")
        return data
