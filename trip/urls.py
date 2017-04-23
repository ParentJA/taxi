# Django imports.
from django.conf.urls import url

# Local imports.
from .apis import UserListView, TripView, TripStatusView

urlpatterns = [
    url(r'users/$', UserListView.as_view(), name='user_list'),
    url(r'^$', TripView.as_view(), name='trip_list'),
    url(r'^(?P<trip_nk>\w+)/$', TripView.as_view(), name='trip_detail'),
    url(r'^(?P<trip_nk>\w+)/status/$', TripStatusView.as_view(), name='trip_status'),
]
