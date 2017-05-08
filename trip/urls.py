# Django imports.
from django.conf.urls import url

# Local imports.
from .apis import TripView

urlpatterns = [
    url(r'^$', TripView.as_view({'get': 'list'}), name='trip_list'),
    url(r'^(?P<trip_nk>\w{32})/$', TripView.as_view({'get': 'retrieve'}), name='trip_detail'),
]
