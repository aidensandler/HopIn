from urllib.parse import quote

from django.contrib import messages
from django.db import transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import (
    CodeRedeemForm,
    NewRideForm,
    RegistrantForm,
    ReviewForm,
    RideForm,
    SortFilterForm,
)
from .models import EventPass, Notification, Person, Registrant, RideRequest, RideReview


def index(request):
    """Search page.

    Searches for drivers by city (origination or destination) and/or destination state.
    Also includes the NewRideForm in the context (Lab 3 requirement).
    """

    context = {}

    city_search = request.GET.get("city", "").strip()
    state_search = request.GET.get("state", "").strip().upper()

    # Sort + filter controls
    sort = request.GET.get("sort", "date")
    service_level = request.GET.get("service_level", "")
    vehicle_type = request.GET.get("vehicle_type", "")
    atmosphere = request.GET.getlist("atmosphere")

    if city_search or state_search:
        context["inputExists"] = True

        queryset = Person.objects.all()

        if city_search:
            city_query = Q(origination__icontains=city_search) | Q(destination_city__icontains=city_search)
            queryset = queryset.filter(city_query)

        if state_search:
            if len(state_search) == 2:
                queryset = queryset.filter(destination_state__iexact=state_search)
            else:
                queryset = Person.objects.none()

        # Filters
        if service_level:
            queryset = queryset.filter(service_level=service_level)
        if vehicle_type:
            queryset = queryset.filter(vehicle_type=vehicle_type)
        if atmosphere:
            # stored as CSV: match each selected token
            for token in atmosphere:
                queryset = queryset.filter(atmosphere_preferences__icontains=token)

        # Sort
        if sort == "seats":
            queryset = queryset.order_by("-seats_available", "date", "time")
        elif sort == "price":
            queryset = queryset.order_by("price", "date", "time")
        elif sort == "premium":
            queryset = queryset.order_by("-service_level", "date", "time")
        else:
            queryset = queryset.order_by("date", "time")

        context["people"] = queryset
    else:
        context["inputExists"] = False
        context["people"] = Person.objects.none()

    # Forms
    context["form"] = RideForm(initial={"city": city_search, "state": state_search})
    context["sort_filter_form"] = SortFilterForm(
        initial={
            "sort": sort,
            "service_level": service_level,
            "vehicle_type": vehicle_type,
            "atmosphere": atmosphere,
        }
    )
    context["new_ride_form"] = NewRideForm()  # Lab 3: add right before render

    # Registration/session info
    context["is_registered"] = request.session.get("registrant_id") is not None
    context["event_destination"] = (
        request.session.get("destination_city"),
        request.session.get("destination_state"),
    )
    context["ride_type"] = request.session.get("ride_type")
    context["event_name"] = request.session.get("event_name")

    return render(request, "index_view.html", context)


def ride_detail(request, person_id):
    """Ride detail page: full info + map + reviews + request button."""

    ride = get_object_or_404(Person, pk=person_id)

    origin = f"{ride.origination}, {ride.origination_state}"
    dest = f"{ride.destination_city}, {ride.destination_state}"
    map_url = (
        "https://www.google.com/maps/dir/?api=1"
        + f"&origin={quote(origin)}&destination={quote(dest)}"
    )

    registrant_id = request.session.get("registrant_id")
    can_review = False
    if registrant_id is not None:
        can_review = RideRequest.objects.filter(
            registrant_id=registrant_id,
            driver=ride,
            status="accepted",
        ).exists()

    return render(
        request,
        "ride_detail.html",
        {
            "ride": ride,
            "map_url": map_url,
            "reviews": ride.reviews.order_by("-created_at"),
            "review_form": ReviewForm(),
            "can_review": can_review,
            "is_registered": registrant_id is not None,
        },
    )


def add_ride(request):
    """Page that contains the 'Post a ride' form (separate from search page)."""
    context = {
        "new_ride_form": NewRideForm(),
        "is_registered": request.session.get("registrant_id") is not None,
        "event_destination": (
            request.session.get("destination_city"),
            request.session.get("destination_state"),
        ),
        "ride_type": request.session.get("ride_type"),
        "event_name": request.session.get("event_name"),
    }
    return render(request, "add_ride.html", context)


def create(request):
    """Create a new ride post from the index page."""
    if request.method == "POST":
        new_ride = NewRideForm(request.POST)
        if new_ride.is_valid():
            new_ride.save()
        else:
            messages.error(request, "Could not create ride. Please check your inputs.")
    return redirect("/rides")


def my_rides(request):
    """Driver management page (simple, session-based).

    We identify the driver by the email they used when posting rides.
    If the current registered user has an email, we show rides posted
    with that same email.
    """

    registrant_id = request.session.get("registrant_id")
    email = ""
    if registrant_id is not None:
        try:
            email = Registrant.objects.get(pk=registrant_id).email
        except Registrant.DoesNotExist:
            email = ""

    rides = Person.objects.none()
    requests = RideRequest.objects.none()
    if email:
        rides = Person.objects.filter(email__iexact=email).order_by("date", "time")
        requests = RideRequest.objects.filter(driver__email__iexact=email).order_by("-created_at")

    return render(
        request,
        "my_rides.html",
        {"rides": rides, "requests": requests, "email": email, "is_registered": registrant_id is not None},
    )


def cancel_ride(request, person_id):
    if request.method != "POST":
        return redirect(reverse("rides:my_rides"))

    registrant_id = request.session.get("registrant_id")
    if registrant_id is None:
        return redirect(reverse("rides:register"))
    registrant = get_object_or_404(Registrant, pk=registrant_id)
    ride = get_object_or_404(Person, pk=person_id)

    if registrant.email and ride.email and registrant.email.lower() == ride.email.lower():
        ride.delete()
        messages.success(request, "Ride deleted.")
    else:
        messages.error(request, "You can only manage rides posted with your email.")
    return redirect(reverse("rides:my_rides"))


def register(request):
    """Manual registration (name/city/state/phone).

    Creates a lightweight Registrant record and stores its id in the session.
    """

    if request.session.get("registrant_id") is not None:
        next_url = request.GET.get("next")
        return redirect(next_url or reverse("rides:index"))

    next_url = request.GET.get("next", "")

    if request.method == "POST":
        form = RegistrantForm(request.POST, request.FILES)
        if form.is_valid():
            registrant = Registrant.objects.create(
                name=form.cleaned_data["name"],
                phone=form.cleaned_data["phone"],
                City=form.cleaned_data["city"],
                State=form.cleaned_data["state"],
                email=form.cleaned_data.get("email") or "",
                profile_pic=form.cleaned_data.get("profile_pic"),
            )
            request.session["registrant_id"] = registrant.id
            request.session["ride_type"] = "free"
            messages.success(request, "You're registered! You can now request rides.")

            posted_next = request.POST.get("next")
            return redirect(posted_next or next_url or reverse("rides:index"))
    else:
        form = RegistrantForm()

    return render(request, "register.html", {"form": form, "next": next_url})


def redeem_code(request):
    """Redeem a one-time event pass (conference/marathon).

    - Checks code exists, matches event_type, is active, and has NOT been redeemed.
    - Auto-registers the user into Registrant.
    - Stores destination + event info in session.
    """

    if request.method == "POST":
        form = CodeRedeemForm(request.POST)
        if form.is_valid():
            ride_type = form.cleaned_data["ride_type"]

            # Free ride path: just redirect to manual registration
            if ride_type == "free":
                return redirect(reverse("rides:register"))

            code = (form.cleaned_data.get("code") or "").strip()
            try:
                p = EventPass.objects.get(
                    code=code,
                    event_type=ride_type,
                    is_active=True,
                    redeemed_at__isnull=True,
                )
            except EventPass.DoesNotExist:
                form.add_error("code", "Invalid code, wrong event type, or code already used.")
                return render(request, "redeem.html", {"form": form})

            # Create registrant record from the pass (auto-fill identity)
            registrant = Registrant.objects.create(
                name=p.full_name,
                phone=p.phone or "",
                City="",
                State="",
                email=p.email or "",
            )

            # Mark the pass as redeemed (one-time)
            p.redeemed_at = timezone.now()
            p.save()

            # Session: remember user + event destination
            request.session["registrant_id"] = registrant.id
            request.session["ride_type"] = ride_type
            request.session["event_name"] = p.event_name
            request.session["destination_city"] = p.destination_city
            request.session["destination_state"] = p.destination_state

            messages.success(request, "Code accepted! You're registered for the event ride.")
            return redirect(reverse("rides:index"))
    else:
        form = CodeRedeemForm()

    return render(request, "redeem.html", {"form": form})


def request_ride(request, person_id):
    """Request a ride from a driver. Requires prior registration."""

    if request.session.get("registrant_id") is None:
        next_url = quote(request.build_absolute_uri(request.get_full_path()), safe="")
        return redirect(reverse("rides:register") + "?next=" + next_url)

    person = get_object_or_404(Person, pk=person_id)
    registrant = get_object_or_404(Registrant, pk=request.session["registrant_id"])

    context = {
        "person": person,
        "driver_start": f"{person.origination}, {person.origination_state}",
        "driver_end": f"{person.destination_city}, {person.destination_state}",
        "user_loc": f"{registrant.City}, {registrant.State}",
        "event_destination": (
            request.session.get("destination_city"),
            request.session.get("destination_state"),
        ),
        "event_name": request.session.get("event_name"),
        "ride_type": request.session.get("ride_type"),
    }
    return render(request, "request_ride.html", context)


def confirm_ride_request(request, person_id):
    """POST-only: create RideRequest, notify driver, show user confirmation."""

    if request.method != "POST":
        return redirect(reverse("rides:index"))

    if request.session.get("registrant_id") is None:
        messages.warning(request, "Please register before requesting a ride.")
        return redirect(reverse("rides:register"))

    driver = get_object_or_404(Person, pk=person_id)
    registrant = get_object_or_404(Registrant, pk=request.session["registrant_id"])

    if driver.seats_available <= 0:
        messages.error(request, "Sorry—this ride is full.")
        return redirect(reverse("rides:ride_detail", args=[driver.id]))

    ride_request = RideRequest.objects.create(registrant=registrant, driver=driver)
    Notification.objects.create(
        driver=driver,
        message=f"{registrant.name} requested a ride with you.",
        ride_request=ride_request,
    )

    messages.success(
        request,
        f"Your request has been sent to {driver.first_name}. They have been notified.",
    )

    return redirect(reverse("rides:ride_detail", args=[driver.id]))


def driver_request_action(request, request_id, action):
    """Driver accepts/declines a ride request."""

    if request.method != "POST":
        return redirect(reverse("rides:my_rides"))

    rr = get_object_or_404(RideRequest, pk=request_id)
    registrant_id = request.session.get("registrant_id")
    if registrant_id is None:
        messages.error(request, "Please register first.")
        return redirect(reverse("rides:register"))

    registrant = get_object_or_404(Registrant, pk=registrant_id)
    if not (registrant.email and rr.driver.email and registrant.email.lower() == rr.driver.email.lower()):
        messages.error(request, "You can only manage requests for rides posted with your email.")
        return redirect(reverse("rides:my_rides"))

    if action == "accept":
        with transaction.atomic():
            driver = Person.objects.select_for_update().get(pk=rr.driver_id)
            if driver.seats_available <= 0:
                rr.status = "declined"
                rr.save()
                messages.error(request, "Ride is full—request declined.")
            else:
                Person.objects.filter(pk=driver.pk).update(seats_available=F("seats_available") - 1)
                rr.status = "accepted"
                rr.save()
                messages.success(request, "Request accepted; seat reserved.")
    elif action == "decline":
        rr.status = "declined"
        rr.save()
        messages.info(request, "Request declined.")

    return redirect(reverse("rides:my_rides"))


def submit_review(request, person_id):
    if request.method != "POST":
        return redirect(reverse("rides:ride_detail", args=[person_id]))

    registrant_id = request.session.get("registrant_id")
    if registrant_id is None:
        messages.error(request, "Please register before leaving a review.")
        return redirect(reverse("rides:register"))

    driver = get_object_or_404(Person, pk=person_id)

    eligible = RideRequest.objects.filter(
        registrant_id=registrant_id,
        driver=driver,
        status="accepted",
    ).exists()
    if not eligible:
        messages.error(request, "You can only review after your ride request is accepted.")
        return redirect(reverse("rides:ride_detail", args=[person_id]))

    form = ReviewForm(request.POST)
    if form.is_valid():
        RideReview.objects.create(
            driver=driver,
            rating=int(form.cleaned_data["rating"]),
            comment=form.cleaned_data.get("comment") or "",
        )
        messages.success(request, "Thanks! Your review was submitted.")
    else:
        messages.error(request, "Please choose a rating.")

    return redirect(reverse("rides:ride_detail", args=[person_id]))
