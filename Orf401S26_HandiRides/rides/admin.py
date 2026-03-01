
from django.contrib import admin

from .models import EventPass, Notification, Person, Registrant, RideRequest, RideReview


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "origination",
        "origination_state",
        "destination_city",
        "destination_state",
        "date",
        "time",
        "seats_available",
        "service_level",
        "vehicle_type",
    )
    search_fields = ("first_name", "last_name", "email", "origination", "destination_city")
    list_filter = ("service_level", "vehicle_type", "origination_state", "destination_state")


@admin.register(Registrant)
class RegistrantAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "City", "State")
    search_fields = ("name", "phone", "email")


@admin.register(RideRequest)
class RideRequestAdmin(admin.ModelAdmin):
    list_display = ("driver", "registrant", "status", "created_at")
    list_filter = ("status",)


@admin.register(RideReview)
class RideReviewAdmin(admin.ModelAdmin):
    list_display = ("driver", "rating", "created_at")
    list_filter = ("rating",)


@admin.register(EventPass)
class EventPassAdmin(admin.ModelAdmin):
    list_display = ("code", "event_type", "event_name", "full_name", "destination_city", "destination_state", "redeemed_at", "is_active")
    search_fields = ("code", "event_name", "full_name", "email")
    list_filter = ("event_type", "is_active")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("driver", "message", "read", "created_at")
    list_filter = ("read",)
