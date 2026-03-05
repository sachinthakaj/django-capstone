from rest_framework import permissions


class IsBookingOwner(permissions.BasePermission):
    """
    Only the user who created the booking (created_by) can view or cancel it.
    """

    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user
