
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.forms import ValidationError

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    service = models.ForeignKey('providers.Service', on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    booking_date = models.DateField()
    number_of_guests = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        "auth.User", related_name="bookings", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.booking_date and self.booking_date <= timezone.now().date():
            raise ValidationError({'booking_date': "Booking date must be in the future."})

    def save(self, *args, **kwargs):
        self.total_price = self.service.price * self.number_of_guests
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking for {self.customer_name} - {self.service.title}"