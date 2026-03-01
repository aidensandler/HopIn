from django.urls import path
from . import views

app_name = 'rides'

urlpatterns = [
    path('', views.index, name='index'),
    path('add/', views.add_ride, name='add_ride'),
    path('create', views.create, name='create'),
    path('<int:person_id>/', views.ride_detail, name='ride_detail'),
    # Existing app functionality (registration + ride requests)
    path('register/', views.register, name='register'),
    path('request/<int:person_id>/', views.request_ride, name='request_ride'),
    path('request/<int:person_id>/confirm/', views.confirm_ride_request, name='confirm_ride_request'),

    # Driver management
    path('my/', views.my_rides, name='my_rides'),
    path('my/<int:person_id>/cancel/', views.cancel_ride, name='cancel_ride'),
    path('my/request/<int:request_id>/<str:action>/', views.driver_request_action, name='driver_request_action'),

    # Reviews
    path('<int:person_id>/review/', views.submit_review, name='submit_review'),

    # Event code redemption (one-time code per person & specific event)
    path('redeem/', views.redeem_code, name='redeem'),
]
