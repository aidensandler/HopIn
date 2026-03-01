from django import forms

from .models import RideReview 
from .models import Person


class RideForm(forms.Form):
    """Search form used on the rides index page.

    Blackboard's starter file only had a single `search` field.
    Your UI uses `city` and `state`, so we keep those fields to avoid
    template errors.
    """

    search = forms.CharField(label="Search term", max_length=64, required=False)
    city = forms.CharField(label="City (Origination or Destination)", max_length=64, required=False)
    state = forms.CharField(label="State (2-letter abbreviation)", max_length=2, required=False)

    def clean_state(self):
        raw = (self.cleaned_data.get("state") or "").strip()
        if raw == "":
            return raw
        raw = raw.upper()
        if len(raw) != 2:
            raise forms.ValidationError("State must be a 2-letter abbreviation (e.g. NJ, MA).")
        return raw


class RegistrantForm(forms.Form):
    """Manual registration form (used when the user does NOT have an event code)."""

    name = forms.CharField(label="Your name", max_length=128)
    phone = forms.CharField(label="Phone number (10 digits)", max_length=20)
    city = forms.CharField(label="City", max_length=255)
    state = forms.CharField(label="State (2-letter abbreviation)", max_length=2)
    email = forms.EmailField(label="Email (optional)", required=False)
    profile_pic = forms.FileField(label="Profile picture (optional)", required=False)

    def clean_state(self):
        raw = (self.cleaned_data.get("state") or "").strip().upper()
        if len(raw) != 2:
            raise forms.ValidationError("State must be a 2-letter abbreviation (e.g. NJ, MA).")
        return raw

    def clean_phone(self):
        raw = (self.cleaned_data.get("phone") or "").strip()
        digits = "".join(c for c in raw if c.isdigit())
        if len(digits) != 10:
            raise forms.ValidationError("Phone number must be exactly 10 digits.")
        return digits


class CodeRedeemForm(forms.Form):
    """Event code redemption: one-time code per person and specific event."""

    ride_type = forms.ChoiceField(
        choices=[
            ("free", "Free ride"),
            ("conference", "Conference ride (code)"),
            ("marathon", "Marathon ride (code)"),
        ],
        initial="free",
        required=True,
    )
    code = forms.CharField(label="Your one-time code", max_length=32, required=False)

    def clean(self):
        cleaned = super().clean()
        ride_type = cleaned.get("ride_type")
        code = (cleaned.get("code") or "").strip()

        if ride_type in ("conference", "marathon") and code == "":
            raise forms.ValidationError("Please enter your conference/marathon code.")
        return cleaned


class NewRideForm(forms.ModelForm):
    """ModelForm used for posting a new ride.

    We intentionally hide fields that a driver should NOT set for themselves:
    - taking_passengers (we infer availability from seats_available)
    - rating (ratings come from rider reviews)
    Also, we provide an 'atmosphere' multi-select (select all that apply).
    """

    ATMOSPHERE_CHOICES = [
        ("music_friendly", "Music-friendly"),
        ("talkative", "Talkative"),
        ("silent", "Silent"),
        ("phone_calls_ok", "Phone calls ok"),
        ("no_phone_calls", "No phone calls"),
    ]

    atmosphere = forms.MultipleChoiceField(
        label="Atmosphere (select all that apply)",
        required=False,
        choices=ATMOSPHERE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Person
        # Hide fields we don't want in the post-a-ride form
        exclude = [
            "taking_passengers",
            "rating",
            "atmospheric_conditions",
            "chat_allowed",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Prepopulate the multi-select from stored CSV
        if self.instance and getattr(self.instance, "atmosphere_preferences", ""):
            self.initial["atmosphere"] = [
                x for x in self.instance.atmosphere_preferences.split(",") if x
            ]

    def save(self, commit=True):
        instance = super().save(commit=False)
        selected = self.cleaned_data.get("atmosphere") or []
        instance.atmosphere_preferences = ",".join(selected)
        if commit:
            instance.save()
            self.save_m2m()
        return instance

class ReviewForm(forms.ModelForm):
    class Meta:
        model = RideReview
        fields = ["rating", "comment"]
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 3, "placeholder": "Write a short review..."})
        }

from django import forms

class SortFilterForm(forms.Form):
    SORT_CHOICES = [
        ("date_asc", "Soonest date"),
        ("date_desc", "Latest date"),
        ("seats_desc", "Most seats"),
        ("premium_first", "Premium first"),
    ]

    sort_by = forms.ChoiceField(choices=SORT_CHOICES, required=False, initial="date_asc")

    vehicle_type = forms.ChoiceField(
        choices=[
            ("", "Any vehicle"),
            ("sedan", "Sedan"),
            ("suv", "SUV"),
            ("van", "Van"),
            ("truck", "Truck"),
            ("other", "Other"),
        ],
        required=False,
    )

    service_level = forms.ChoiceField(
        choices=[
            ("", "Any tier"),
            ("regular", "Regular CartyCity"),
            ("premium", "Premium CartyCity"),
        ],
        required=False,
    )

    # “select all that apply” atmosphere filters (optional)
    atmosphere = forms.MultipleChoiceField(
        choices=[
            ("music", "Music-friendly"),
            ("talkative", "Talkative"),
            ("silent", "Silent"),
            ("calls_ok", "Phone calls ok"),
            ("no_calls", "No phone calls"),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )