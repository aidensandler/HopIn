from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Person(models.Model):
  first_name = models.CharField(max_length=64)
  last_name = models.CharField(max_length=64, default='', blank=True)
  email = models.EmailField(blank=True, null=True)
  origination = models.CharField(max_length=64)
  origination_state = models.CharField(max_length=2)
  destination_city = models.CharField(max_length=64)
  destination_state = models.CharField(max_length=2)
  date = models.DateField()
  time = models.TimeField()
  taking_passengers = models.BooleanField(default=False)
  seats_available = models.IntegerField(default=0)
  # Atmosphere preferences (stored as comma-separated values)
  atmosphere_preferences = models.CharField(max_length=128, blank=True, default='')
  # Driver profile (for ride request page)
  photo = models.ImageField(upload_to='driver_photos/', blank=True, null=True)
  rating = models.DecimalField(max_digits=2, decimal_places=1, default=0, help_text='Driver rating 0–5')
  car_make = models.CharField(max_length=64, blank=True)
  car_model = models.CharField(max_length=64, blank=True)
  price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text='Price per seat (TBD if null)')
  luggage_available = models.BooleanField(default=False, help_text='Does the driver have luggage space available?')
  atmospheric_conditions = models.CharField(max_length=64, blank=True, help_text='What are the drivers preferred atmospheric conditions? (e.g. talkative, quiet, music-friendly, etc.)')
  chat_allowed = models.BooleanField(default=False, help_text='Is chat allowed in the car?')

  class VehicleType(models.TextChoices):
    SEDAN = 'sedan', 'Sedan'
    SUV = 'suv', 'SUV'
    VAN = 'van', 'Van'
    TRUCK = 'truck', 'Truck'
    OTHER = 'other', 'Other'

  vehicle_type = models.CharField(
    max_length=12,
    choices=VehicleType.choices,
    default=VehicleType.SEDAN,
  )

  class ServiceLevel(models.TextChoices):
    REGULAR = 'regular', 'Regular CartyCity'
    PREMIUM = 'premium', 'Premium CartyCity'

  service_level = models.CharField(
    max_length=12,
    choices=ServiceLevel.choices,
    default=ServiceLevel.REGULAR,
  )

  def __str__(self):
    name = (self.first_name + ' ' + (self.last_name or '')).strip()
    return f"{name or 'Driver'}: {self.origination}, {self.origination_state} → {self.destination_city}, {self.destination_state} on {self.date}"

  @property
  def atmosphere_list(self):
    """List of atmosphere preference keys."""
    raw = (self.atmosphere_preferences or '').strip()
    if not raw:
      return []
    return [x for x in raw.split(',') if x]

  @property
  def average_rating(self):
    """Average of all rider reviews (None if no reviews yet)."""
    if not hasattr(self, 'reviews'):
      return None
    qs = self.reviews.all()
    if not qs.exists():
      return None
    total = sum([r.rating for r in qs])
    return round(total / qs.count(), 1)


class Registrant(models.Model):
  """User registration; required before requesting a ride."""
  name = models.CharField(max_length=128)
  phone = models.CharField(max_length=10, help_text='Exactly 10 digits')
  email = models.EmailField(blank=True)
  City = models.CharField(max_length=255)
  State = models.CharField(max_length=2)
  profile_pic = models.FileField(upload_to='registrants/', blank=True, null=True)


class RideRequest(models.Model):
  """A registrant's request to ride with a driver. Creates a notification for the driver."""
  registrant = models.ForeignKey(Registrant, on_delete=models.CASCADE)
  driver = models.ForeignKey(Person, on_delete=models.CASCADE)
  created_at = models.DateTimeField(auto_now_add=True)
  status = models.CharField(max_length=20, default='pending')  # e.g. pending, accepted, declined




class RideReview(models.Model):
  """A rider review for a driver (Person)."""
  driver = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='reviews')
  rating = models.PositiveSmallIntegerField()
  comment = models.CharField(max_length=255, blank=True, default='')
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return f"{self.driver} - {self.rating}"

class Notification(models.Model):
  """In-app notification for driver when someone requests a ride."""
  driver = models.ForeignKey(Person, on_delete=models.CASCADE)
  message = models.CharField(max_length=255)
  ride_request = models.ForeignKey(RideRequest, on_delete=models.CASCADE, null=True, blank=True)
  read = models.BooleanField(default=False)
  created_at = models.DateTimeField(auto_now_add=True)

class UserProfile(models.Model):
  user = models.OneToOneField(User, on_delete=models.CASCADE)

  full_name = models.CharField(max_length=100)
  phone = models.CharField(max_length=20)
  email = models.EmailField(blank=True, null=True)
  profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

  def __str__(self):
      return self.full_name


class EventPass(models.Model):
  """One-time code per person and specific event.

  Users with a pass can enter their code and get auto-registered, with their
  destination stored by the app.
  """

  class EventType(models.TextChoices):
    CONFERENCE = 'conference', 'Conference'
    MARATHON = 'marathon', 'Marathon'

  code = models.CharField(max_length=32, unique=True)
  event_type = models.CharField(max_length=16, choices=EventType.choices)
  event_name = models.CharField(max_length=128)

  full_name = models.CharField(max_length=128)
  phone = models.CharField(max_length=10, blank=True, default='')
  email = models.EmailField(blank=True, null=True)

  destination_city = models.CharField(max_length=64)
  destination_state = models.CharField(max_length=2)

  redeemed_at = models.DateTimeField(blank=True, null=True)
  is_active = models.BooleanField(default=True)

  def __str__(self):
    return f"{self.code} ({self.event_name})"
