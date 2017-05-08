# Uber App Using Django Channels

## Introduction

## Authentication

Authentication is the cornerstone of any app that handles user data. It allows users to maintain privacy within the app, while gaining access to the full set of features afforded with registration.

With Django REST Framework (DRF), we have three authentication classes to choose from: `BasicAuthentication`, `TokenAuthentication`, and `SessionAuthentication`. We can eliminate `BasicAuthentication` right off the bat because it doesn't offer enough security for production environments. Between the remaining two classes, we choose `TokenAuthentication` because it offers the best support for both desktop and mobile clients. The idea is simple--the server generates a token for a user on login and that token can be used from any device to gain access to protected APIs.

Let's start by setting up our app to allow token-based authentication. We install the `rest_framework` and `rest_framework.authtoken` apps and we tell DRF to use `TokenAuthentication` by default.

**taxi/settings.py**

```python
ALLOWED_HOSTS = ['*']

DJANGO_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework.authtoken',
]

LOCAL_APPS = [
    'trip',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    )
}
```

We need to run the `migrate` management command to set up our database and install the DRF authentication tables.

```bash
$ python manage.py migrate
```

During the course of this tutorial, we are going to be following test-driven development (TDD) to confirm that our code works. In the next part of the tutorial, we will be adding a user interface so that we can play with the app as an actual user.

Let's start by creating a new user account via an API. A user should be able to download our app and immediately sign up for a new account by providing the bare minimum of information--a username and a password. The distinction between `password1` and `password2` correlates to a user entering her password and then confirming it. Eventually, our app will present the user with a form with username and password fields and a submit button. 

Note that throughout this tutorial, we will only be testing the happy paths. Adding tests for error handling is a separate exercise left to the reader.

**trip/tests.py**

```python
from django.contrib.auth import get_user_model
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_201_CREATED
from rest_framework.test import APIClient, APITestCase
from .serializers import PublicUserSerializer

PASSWORD = 'pAssw0rd!'


class AuthenticationTest(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_user_can_sign_up(self):
        response = self.client.post(reverse('sign_up'), data={
            'username': 'user@example.com',
            'password1': PASSWORD,
            'password2': PASSWORD
        })
        user = get_user_model().objects.last()
        self.assertEqual(HTTP_201_CREATED, response.status_code)
        self.assertEqual(PublicUserSerializer(user).data, response.data)
```

A couple things to note: 1) we expect our API to return a 201 status code when the user account is created, and 2) we are leveraging DRF's serializers to convert between objects and JSON strings. We expect the response payload to be a JSON-serialized user account.

When we run our first test, it fails. Remember, a tenant of TDD is that we should write failing tests before writing the code to get them to pass. 

```bash
$ python manage.py test trip.tests
```

We need to create several pieces of code before our tests will pass. Typically, a data model is the first thing we want to create in a situation like this, however, we are leveraging Django's user model for simplicity so there is no reason to create that code. In this case, the first bit of code we create is the user serializer. Remember, right now our user data is basic (username and password), so we only need access to a couple of fields. We should never need to read the password.

**trip/serializers.py**

```python
from django.contrib.auth import get_user_model
from rest_framework import serializers


class PublicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username',)
```

The simplicity of our user data is reflected in our `SignUpView`. We pass the data to Django's `UserCreationForm`, which expects only username and password. If the form is valid, we save the user and pass the serialized data back to the client with a success status. If the form validation fails, we pass back the errors with an error. Form validation could fail if the username is already taken or the password isn't strong enough.

**trip/apis.py**

```python
from django.contrib.auth.forms import UserCreationForm
from rest_framework import status, views
from rest_framework.response import Response
from .serializers import PublicUserSerializer


class SignUpView(views.APIView):
    def post(self, *args, **kwargs):
        form = UserCreationForm(data=self.request.data)
        if form.is_valid():
            user = form.save()
            return Response(PublicUserSerializer(user).data, status=status.HTTP_201_CREATED)
        else:
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
```

We finish our task by configuring a URL to link to our view.

**taxi/urls.py**

```python
from django.conf.urls import url
from .apis import SignUpView

urlpatterns = [
    url(r'^api/sign_up/$', SignUpView.as_view(), name='sign_up'),
]
```

Now, when we run the tests, they pass!

```bash
$ python manage.py test trip.tests
```

Now that we can sign up a new user, the next logical step is to create the functionality to log the user in and out. We start with two new tests to handle the log in and log out behavior respectively. Note that we also added a `create_user()` helper function to help keep our code DRY. When a user logs in, the server should create a token for that user. By including that token in the request headers of future requests, the user can access other APIs. The token should be deleted when the user logs out.

**trip/tests.py**

```python
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT
from rest_framework.test import APITestCase
from .serializers import PrivateUserSerializer


def create_user(username='user@example.com', password=PASSWORD):
    return get_user_model().objects.create_user(username=username, password=password)


class AuthenticationTest(APITestCase):
    def test_user_can_log_in(self):
        user = create_user()
        response = self.client.post(reverse('log_in'), data={
            'username': user.username,
            'password': PASSWORD,
        })
        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(PrivateUserSerializer(user).data, response.data)
        self.assertIsNotNone(Token.objects.get(user=user))

    def test_user_can_log_out(self):
        user = create_user()
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        self.client.login(username=user.username, password=self.password)
        response = self.client.post(reverse('log_out'))
        self.assertEqual(HTTP_204_NO_CONTENT, response.status_code)
        self.assertFalse(Token.objects.filter(user=user).exists())
```

The process of logging in is as easy as signing up. The user enters her username and password and submits them to the server. We expect the server to log the user in and then return a success status along with the serialized user data. At this point, we can confirm that a token has been created for the user.

Logging out is even simpler. The user should be logged out when she hits the appropriate API and her token should be deleted.

Run the tests and watch them fail.

```bash
$ python manage.py test trip.tests
```

Now that tokens are being created, we should have two different user serializers--one for public consumption and one for private use. Only the logged-in user should be able to receive her token. Other users can see each others' basic information, but that's it! We serve our app over HTTPS, so there is little concern about someone stealing our token from our private response payload.

**trip/serializers.py**

```python
from django.contrib.auth import get_user_model
from rest_framework import serializers


class PrivateUserSerializer(PublicUserSerializer):
    class Meta(PublicUserSerializer.Meta):
        fields = list(PublicUserSerializer.Meta.fields) + ['auth_token']
```

We program our log in and log out functions as we planned in the tests. Let's break each view down. In our `LogInView`, we leverage Django's `AuthenticationForm`, which expects username and password data to be provided. We validate the form to get an existing user and then we log that user in. Next, we create a token. Note that using `get_or_create()` allows us to avoid having to generate a new token every time a logged-in user hits the "log in" API.

Our `LogOutView` does the opposite of the `LogInView`; it logs the user out and deletes her token. We add an `IsAuthenticated` permission to ensure that only logged-in users can log out.

**trip/apis.py**

```python
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from rest_framework import permissions, status, views
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from .serializers import PrivateUserSerializer


class LogInView(views.APIView):
    def post(self, *args, **kwargs):
        form = AuthenticationForm(data=self.request.data)
        if form.is_valid():
            user = form.get_user()
            login(self.request, user)
            Token.objects.get_or_create(user=user)
            return Response(PrivateUserSerializer(user).data)
        else:
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)


class LogOutView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, *args, **kwargs):
        logout(self.request)
        Token.objects.get(user=self.request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
```

We link our new views to URLs in the existing configuration.

**taxi/urls.py**

```python
from django.conf.urls import url
from trip.apis import SignUpView, LogInView, LogOutView

urlpatterns = [
    url(r'^api/sign_up/$', SignUpView.as_view(), name='sign_up'),
    url(r'^api/log_in/$', LogInView.as_view(), name='log_in'),
    url(r'^api/log_out/$', LogOutView.as_view(), name='log_out'),
]
```

We run our authentication tests one last time to make sure they pass. Our authentication work is done!

```bash
$ python manage.py test trip.tests
```

## HTTP

After a user logs in, she should be taken to a dashboard that displays an overview of her user-related data. Even though we plan to use WebSockets for user-to-user communication, we still have a use for run-of-the-mill HTTP requests. Users should be able to query the server for information about their past, present, and future trips. Up-to-date information is vital to understanding where the user has travelled from or for planning where she is travelling next.

Our HTTP-related tests capture these scenarios. First, let's add a feature to let a user view all of the trips associated with her account. As an initial step, we will allow a user to see all existing trips; later on in this tutorial, we will add better filtering. 

**trip/tests.py**

```python
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APIClient, APITestCase
from .models import Trip
from .serializers import TripSerializer


class HttpTripTest(APITestCase):
    def setUp(self):
        user = create_user()
        token = Token.objects.create(user=user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

    def test_user_can_list_trips(self):
        trips = [
            Trip.objects.create(pick_up_address='A', drop_off_address='B'),
            Trip.objects.create(pick_up_address='B', drop_off_address='C')
        ]
        response = self.client.get(reverse('trip:trip_list'))
        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(TripSerializer(trips, many=True).data, response.data)
```

As you can see, we are authenticating the user with her token via an authorization header. Our test creates two trips and then makes a call to the "trip list" API, which should successfully return the trip data.

For now, as tests fail.

```bash
$ python manage.py test trip.tests
```

We have a lot of work to do in order to get the tests passing. First, we need to create a model that represents the concept of a trip. A trip is simply a transportation event between a starting location and a destination, so we should keep track of a pick-up address and a drop-off address. At any given point in time, a trip can be in a specific state, so we should add a status to identify whether a trip is requested, started, in progress, or completed. Lastly, we should have a consistent way to identify and track our trips that is also difficult for someone to guess. We can use an MD5 hash as a natural key for our `Trip` model.

**trip/models.py**

```python
import datetime
import hashlib
from django.db import models
from django.shortcuts import reverse


class Trip(models.Model):
    REQUESTED = 'REQUESTED'
    STARTED = 'STARTED'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    STATUSES = (
        (REQUESTED, REQUESTED),
        (STARTED, STARTED),
        (IN_PROGRESS, IN_PROGRESS),
        (COMPLETED, COMPLETED),
    )

    nk = models.CharField(max_length=32, unique=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    pick_up_address = models.CharField(max_length=255)
    drop_off_address = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUSES, default=REQUESTED)

    def __str__(self):
        return self.nk

    def get_absolute_url(self):
        return reverse('trip:trip_detail', kwargs={'trip_nk': self.nk})

    def save(self, **kwargs):
        if not self.nk:
            now = datetime.datetime.now()
            secure_hash = hashlib.md5()
            secure_hash.update(f'{now}:{self.pick_up_address}:{self.drop_off_address}'.encode('utf-8'))
            self.nk = secure_hash.hexdigest()
        super().save(**kwargs)
```

We want our model to generate natural keys on its own, based on the time that the record is created and the pick-up and drop-off addresses. We will enforce this later on with our `Trip` serializer.

Let's make a migration for our new model and run it to create the corresponding table.

```bash
$ python manage.py makemigrations
$ python manage.py migrate
```

Like the user data, we need a way to serialize the trip data to pass it between the client and the server. By identifying certain fields as "read only", we can ensure that they will never be created or updated via the serializer. In this case, we want the server to be responsible for creating the `id`, `nk`, `created`, and `updated` fields.

**trip/serializers.py**

```python
from rest_framework import serializers
from .models import Trip


class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = '__all__'
        read_only_fields = ('id', 'nk', 'created', 'updated',)
```

As you can see, our `TripView` is incredibly basic. We leverage the DRF `ReadOnlyModelViewSet` to support our trip list and trip detail views. For now, our view will return all trips. Note that like the `LogOutView`, a user needs to be authenticated in order to access this API.

**trip/apis.py**

```python
from rest_framework import permissions, viewsets
from .models import Trip
from .serializers import TripSerializer


class TripView(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
```

We include our trip-specific URL configuration in the main `urls.py` file.

**taxi/urls.py**

```python
from django.conf.urls import include, url
from trip.apis import SignUpView, LogInView, LogOutView

urlpatterns = [
    url(r'^api/sign_up/$', SignUpView.as_view(), name='sign_up'),
    url(r'^api/log_in/$', LogInView.as_view(), name='log_in'),
    url(r'^api/log_out/$', LogOutView.as_view(), name='log_out'),
    url(r'^api/trip/', include('trip.urls', namespace='trip')),
]
```

Our first trip-specific URL enables our `TripView` to provide a list of trips.

**trip/urls.py**

```python
from django.conf.urls import url
from .apis import TripView

urlpatterns = [
    url(r'^$', TripView.as_view({'get': 'list'}), name='trip_list'),
]
```

When we run our tests again, we get our list of trips.

```bash
$ python manage.py test trip.tests
```

Our next and last HTTP test covers the trip detail feature. With this feature, users are able to retrieve the details of a trip identified by it's natural key (`nk`) value.

**trip/tests.py**

```python
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APITestCase
from .models import Trip
from .serializers import TripSerializer


class HttpTripTest(APITestCase):
    def test_user_can_retrieve_trip_by_nk(self):
        trip = Trip.objects.create(pick_up_address='A', drop_off_address='B')
        response = self.client.get(trip.get_absolute_url())
        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(TripSerializer(trip).data, response.data)
```

We leverage the use of the handy `get_absolute_url()` function on our `Trip` model to identify the location of our `Trip` resource. We expect to get the serialized data of a single trip and a success status.

Of course, we create a failing test to begin.

```bash
$ python manage.py test trips.tests
```

Supporting our new functionality is as easy as adding two variables to our `TripView`. The `lookup_field` variable tells the view to get the trip record by its `nk` value. The `lookup_url_kwarg` variable tells the view what named parameter to use to extract the `nk` value from the URL.

**trip/apis.py**

```python
from rest_framework import permissions, viewsets
from .models import Trip
from .serializers import TripSerializer


class TripView(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'nk'
    lookup_url_kwarg = 'trip_nk'
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
```

In our URL configuration, we identify a `trip_nk` that should be 32 characters long, which is the length of the MD5 hash. We link our `TripView` with our new URL.

**trip/urls.py**

```python
from django.conf.urls import url
from .apis import TripView

urlpatterns = [
    url(r'^$', TripView.as_view({'get': 'list'}), name='trip_list'),
    url(r'^(?P<trip_nk>\w{32})/$', TripView.as_view({'get': 'retrieve'}), name='trip_detail'),
]
```

We achieve success when we run our tests again.

```bash
$ python manage.py test trip.tests
```

## WebSockets

Finally, we get to the new and exciting stuff! Using WebSockets, we can allow two users to communicate with each other. The intention is that a trip is shared between a driver and a rider. The rider requests a trip, the driver accepts it, and then the driver updates the status of the trip as appropriate.

The first step is to install and enable Django Channels.

**taxi/settings.py**

```python
THIRD_PARTY_APPS = [
    'channels',
    'rest_framework',
    'rest_framework.authtoken',
]

WSGI_APPLICATION = 'taxi.asgi.application'

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'asgi_redis.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
        },
        'ROUTING': 'taxi.routing.channel_routing',
    },
}
```

We switch from a typical WSGI file to an ASGI file.

**taxi/asgi.py**

```python
import os
from channels import asgi

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi.settings')

channel_layer = asgi.get_channel_layer()
```

We set up our routing layer, which is a reflection of the Django URL configuration. For now, we leave it empty.

**taxi/routing.py**

```python
channel_routing = []
```

We create our first WebSockets test. Notice that we are using a new test case type, `ChannelTestCase`, and a new test client, `HttpClient`. The first step we take is to create two new users, a driver and a rider. Then we set up our tests to make sure that each user can successfully connect with the server via WebSockets.

**trip/tests.py**

```python
from django.contrib.auth import get_user_model
from channels.test import ChannelTestCase, HttpClient


class WebSocketTripTest(ChannelTestCase):
    def setUp(self):
        self.driver = create_user('driver@example.com')
        self.rider = create_user('rider@example.com')

    def connect_as_driver(self, driver):
        client = HttpClient()
        client.login(username=driver.username, password=PASSWORD)
        client.send_and_consume('websocket.connect', path='/driver/')
        return client

    def connect_as_rider(self, rider):
        client = HttpClient()
        client.login(username=rider.username, password=PASSWORD)
        client.send_and_consume('websocket.connect', path='/rider/')
        return client

    def test_driver_can_connect_via_websockets(self):
        client = self.connect_as_driver(self.driver)
        message = client.receive()
        self.assertIsNone(message)

    def test_rider_can_connect_via_websockets(self):
        client = self.connect_as_rider(self.rider)
        message = client.receive()
        self.assertIsNone(message)
```

Since we don't have any code yet, the tests fail.

```bash
python manage.py test trip.tests
```

We need to expand our existing `Trip` model in an important way, in order to track the driver and the rider associated with a trip. Drivers and riders are just regular users. Later on, we will see how the same app can serve two types of users and give each a unique experience.

**trip/models.py**

```python
from django.conf import settings


class Trip(models.Model):
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='trips_as_driver')
    rider = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='trips_as_rider')
```

Again, we make and run migrations to udpdate our table.

```bash
$ python manage.py makemigrations
$ python manage.py migrate
```

Here are our first consumers. We start off with the bare minimum. We create a `DriverConsumer` and a `RiderConsumer` that both inherit from a common `TripConsumer`. Both consumers for drivers and riders will share similar code.

**trip/consumers.py**

```python
from channels.generic.websockets import JsonWebsocketConsumer


class TripConsumer(JsonWebsocketConsumer):
    def connect(self, message, **kwargs):
        self.message.reply_channel.send({'accept': True})


class DriverConsumer(TripConsumer):
    pass


class RiderConsumer(TripConsumer):
    pass
```

We hook up the proper routing.

**taxi/routing.py**

```python
from channels import route_class
from trip.consumers import DriverConsumer, RiderConsumer


channel_routing = [
    route_class(DriverConsumer, path=r'^/driver/$'),
    route_class(RiderConsumer, path=r'^/rider/$'),
]
```

When we run our tests, they pass.

```bash
$ python manage.py test trip.tests
```

Let's get into some more advanced functionality. We need our rider to be able to request a new trip.

**trip/tests.py**

```python
from channels.test import ChannelTestCase
from .models import Trip
from .serializers import TripSerializer


class WebSocketTripTest(ChannelTestCase):
    def test_rider_can_create_trips(self):
        client = self.connect_as_rider(self.rider)
        client.send_and_consume('websocket.receive', path='/rider/', content={
            'text': {
                'pick_up_address': 'A',
                'drop_off_address': 'B',
                'rider': PublicUserSerializer(self.rider).data
            }
        }})
        message = client.receive()
        trip = Trip.objects.last()
        self.assertEqual(TripSerializer(trip).data, message)
```

At this point, the tests will fail.

```bash
$ python manage.py test trip.tests
```

Next, we modify our user serializers a little bit to avoid duplicate code. We also modify our `TripSerializer` to handle driver and rider data on creation.

**trip/serializers.py**

```python
from django.contrib.auth import get_user_model
from rest_framework import serializers


class PublicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username',)
        read_only_fields = ('username',)


class PrivateUserSerializer(PublicUserSerializer):
    class Meta(PublicUserSerializer.Meta):
        fields = list(PublicUserSerializer.Meta.fields) + ['auth_token']


class TripSerializer(serializers.ModelSerializer):
    driver = UserSerializer(allow_null=True, required=False)
    rider = UserSerializer(allow_null=True, required=False)

    def create(self, validated_data):
        data = validated_data.pop('rider', None)
        trip = super().create(validated_data)
        if data:
            trip.rider = get_user_model().objects.get(**data)
        trip.save()
        return trip
```

Let's create a `receive()` function to handle the business logic when a rider requests a new trip. We want to convert the data we receive into a new `Trip` object. Then, we'll send the full serialized trip data back to the client. The client can use this data to update the UI.

**trip/consumers.py**

```python
from channels.generic.websockets import JsonWebsocketConsumer
from .serializers import TripSerializer


class RiderConsumer(TripConsumer):
    def receive(self, content, **kwargs):
        serializer = TripSerializer(data=content)
        serializer.is_valid(raise_exception=True)
        trip = serializer.create(serializer.validated_data)
        self.send(content=TripSerializer(trip).data)
```

Running the tests again, we confirm that we can indeed create a new trip via WebSockets.

```bash
$ python manage.py test trip.tests
```

We abstract the trip creation out into its own helper function. We also add a new test to prove that a rider automatically subscribes to a trip channel when he requests a new trip.

**trip/tests.py**

```python
from channels.test import ChannelTestCase
from .models import Trip
from .serializers import PublicUserSerializer, TripSerializer


class WebSocketTripTest(ChannelTestCase):
    def create_trip(self, rider, pick_up_address='A', drop_off_address='B'):
        client = self.connect_as_rider(rider)
        client.send_and_consume('websocket.receive', path='/rider/', content={
            'text': {
                'pick_up_address': pick_up_address,
                'drop_off_address': drop_off_address,
                'rider': PublicUserSerializer(rider).data
            }
        })
        return client

    def test_rider_can_create_trips(self):
        client = self.create_trip(self.rider)
        message = client.receive()
        trip = Trip.objects.last()
        self.assertEqual(TripSerializer(trip).data, message)

    def test_rider_is_subscribed_to_trip_channel_on_creation(self):
        client = self.create_trip(self.rider)
        client.receive()
        trip = Trip.objects.last()
        message = {'detail': 'This is a test message.'}
        Group(trip.nk).send(message)
        self.assertEqual(message, client.receive())
```

We run our failing test.

```bash
python manage.py test trip.tests
```

We expand our `RiderConsumer` logic to enable the channel subscription. We also beef up the `TripConsumer` connection logic to handle channel subscription.

**trip/consumers.py**

```python
from channels import Group
from channels.generic.websockets import JsonWebsocketConsumer
from .models import Trip
from .serializers import TripSerializer


class TripConsumer(JsonWebsocketConsumer):
    http_user_and_session = True

    def user_trips(self):
        raise NotImplementedError()

    def connect(self, message, **kwargs):
        self.message.reply_channel.send({'accept': True})
        if self.message.user.is_authenticated:
            trip_nks = [trip.nk for trip in self.user_trips()]
            self.message.channel_session['trip_nks'] = trip_nks
            for trip_nk in trip_nks:
                Group(trip_nk).add(self.message.reply_channel)

    def disconnect(self, message, **kwargs):
        for trip_nk in message.channel_session.get('trip_nks', []):
            Group(trip_nk).discard(message.reply_channel)


class RiderConsumer(TripConsumer):
    def user_trips(self):
        return self.message.user.trips_as_rider.exclude(status=Trip.COMPLETED)

    def receive(self, content, **kwargs):
        serializer = TripSerializer(data=content)
        serializer.is_valid(raise_exception=True)
        trip = serializer.create(serializer.validated_data)
        self.message.channel_session['trip_nks'].append(trip.nk)
        Group(trip.nk).add(self.message.reply_channel)
        trips_data = TripSerializer(trip).data
        self.group_send(name=trip.nk, content=trips_data)
```

Run the tests.

```bash
python manage.py test trip.tests
```

OK, time for some driver tests and functionality. First, we make sure that a driver can update a trip and is automatically subscribed to a trip's channel when he accepts a trip.

**trip/tests.py**

```python
from django.contrib.auth import get_user_model
from channels.test import ChannelTestCase
from .models import Trip
from .serializers import TripSerializer


class WebSocketTripTest(ChannelTestCase):
    def update_trip(self, driver, status):
        client = self.connect_as_driver(driver)
        client.send_and_consume('websocket.receive', path='/driver/', content={
            'text': {
                'nk': trip.nk,
                'pick_up_address': trip.pick_up_address,
                'drop_off_address': trip.drop_off_address,
                'status': status,
                'driver': UserSerializer(driver).data
            }
        })
        return client

    def test_driver_can_update_trips(self):
        trip = Trip.objects.create(pick_up_address='A', drop_off_address='B')
        client = self.update_trip(self.driver, trip=trip, status=Trip.STARTED)
        trip = Trip.objects.get(nk=trip.nk)
        self.assertEqual(TripSerializer(trip).data, client.receive())

    def test_driver_is_subscribed_to_trip_channel_on_update(self):
        trip = Trip.objects.create(pick_up_address='A', drop_off_address='B')
        client = self.update_trip(self.driver, trip=trip, status=Trip.STARTED)
        client.receive()
        trip = Trip.objects.last()
        message = {'detail': 'This is a test message.'}
        Group(trip.nk).send(message)
        self.assertEqual(message, client.receive())
```

Failing tests, same story.

```bash
$ python manage.py test trip.tests
```

We add the ability to update a trip.

**trip/serializers.py**

```python
from django.contrib.auth import get_user_model
from rest_framework import serializers


class TripSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        data = validated_data.pop('driver', None)
        if data:
            instance.driver = get_user_model().objects.get(**data)
        instance = super().update(instance, validated_data)
        return instance
```

We flesh out the `DriverConsumer` logic.

**trip/consumers.py**

```python
from channels import Group
from .models import Trip
from .serializers import TripSerializer


class DriverConsumer(TripConsumer):
    groups = ['drivers']

    def user_trips(self):
        return self.message.user.trips_as_driver.exclude(status=Trip.COMPLETED)

    def connect(self, message, **kwargs):
        super().connect(message, **kwargs)
        Group('drivers').add(self.message.reply_channel)

    def receive(self, content, **kwargs):
        trip = Trip.objects.get(nk=content.get('nk'))
        serializer = TripSerializer(data=content)
        serializer.is_valid(raise_exception=True)
        trip = serializer.update(trip, serializer.validated_data)
        self.message.channel_session['trip_nks'].append(trip.nk)
        Group(trip.nk).add(self.message.reply_channel)
        trips_data = TripSerializer(trip).data
        self.group_send(name=trip.nk, content=trips_data)
```

Tests pass.

```bash
$ python manage.py test trip.tests
```

Final tests. We want to make sure that all drivers are alerted when a rider requests a new ride. We also want to make sure that the rider who requests the trip is alerted when a driver starts the trip.

**trip/tests.py**

```python
from channels.test import ChannelTestCase
from .models import Trip
from .serializers import TripSerializer


class WebSocketTripTest(ChannelTestCase):
    def test_driver_is_alerted_on_trip_creation(self):
        client = self.connect_as_driver(self.driver)
        self.create_trip(self.rider)
        trip = Trip.objects.last()
        self.assertEqual(TripSerializer(trip).data, client.receive())

    def test_rider_is_alerted_on_trip_update(self):
        client = self.create_trip(self.rider)
        client.receive()
        trip = Trip.objects.last()
        self.update_trip(self.driver, trip=trip, status=Trip.STARTED)
        trip = Trip.objects.get(nk=trip.nk)
        self.assertEqual(TripSerializer(trip).data, client.receive())
```

The `DriverConsumer` is already equipped to alert the rider. We need to modify the `RiderConsumer` to broadcast the alert to all of the drivers.

**trip/consumers.py**

```python
from channels import Group
from .serializers import TripSerializer


class RiderConsumer(TripConsumer):
    def receive(self, content, **kwargs):
        serializer = TripSerializer(data=content)
        serializer.is_valid(raise_exception=True)
        trip = serializer.create(serializer.validated_data)
        self.message.channel_session['trip_nks'].append(trip.nk)
        Group(trip.nk).add(self.message.reply_channel)
        trips_data = TripSerializer(trip).data
        self.group_send(name=trip.nk, content=trips_data)
        self.group_send(name='drivers', content=trips_data)
```

## UI Support

Up until now, we haven't had a reason to track users as drivers or riders. Users can be anything. But as soon as we add a UI, we will need a way for users to sign up with a role. Drivers will see different UI and will experience different functionality than riders.

The first thing we need to do is add support for user groups in our serializers.

**trip/serializers.py**

```python
from django.contrib.auth import get_user_model
from rest_framework import serializers


class PublicUserSerializer(serializers.ModelSerializer):
    groups = serializers.SlugRelatedField(slug_field='name', many=True, read_only=True)

    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'groups',)
        read_only_fields = ('username',)
```

Next, we prepare our `SignUpView` to assign a user group during the creation of a new user.

**trip/apis.py**

```python
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from rest_framework import status, views
from rest_framework.response import Response
from .serializers import PublicUserSerializer


class SignUpView(views.APIView):
    def post(self, *args, **kwargs):
        group = self.request.data.pop('group', 'rider')
        user_group, _ = Group.objects.get_or_create(name=group)
        form = UserCreationForm(data=self.request.data)
        if form.is_valid():
            user = form.save()
            user.groups.add(user_group)
            user.save()
            return Response(PublicUserSerializer(user).data, status=status.HTTP_201_CREATED)
        else:
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
```

Lastly, we change our `TripView` to add the proper filters.

**trip/apis.py**

```python
from django.db.models import Q
from rest_framework import viewsets
from .models import Trip


class TripView(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        user = self.request.user
        user_groups = [group.name for group in user.groups.all()]
        if 'driver' in user_groups:
            return self.queryset.filter(Q(status=Trip.REQUESTED) | Q(driver=user))
        if 'rider' in user_groups:
            return self.queryset.filter(rider=user)
        return self.queryset.none()
```

When we rerun our tests, we notice that some of them break now.

```bash
$ python manage.py test trip.tests
```

We modify our tests to get them passing. Notice that we modify our `create_user()` function to take an additional `group` parameter.

**trip/tests.py**

```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group as AuthGroup
from channels.test import ChannelTestCase
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APIClient, APITestCase
from .models import Trip
from .serializers import TripSerializer


def create_user(username='user@example.com', password=PASSWORD, group='rider'):
    auth_group, _ = AuthGroup.objects.get_or_create(name=group)
    user = get_user_model().objects.create_user(username=username, password=password)
    user.groups.add(auth_group)
    user.save()
    return user


class HttpTripTest(APITestCase):
    def setUp(self):
        self.user = create_user()
        token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

    def test_user_can_list_personal_trips(self):
        trips = [
            Trip.objects.create(pick_up_address='A', drop_off_address='B', rider=self.user),
            Trip.objects.create(pick_up_address='B', drop_off_address='C', rider=self.user),
            Trip.objects.create(pick_up_address='C', drop_off_address='D')
        ]
        response = self.client.get(reverse('trip:trip_list'))
        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(TripSerializer(trips[0:2], many=True).data, response.data)

    def test_user_can_retrieve_personal_trip_by_nk(self):
        trip = Trip.objects.create(pick_up_address='A', drop_off_address='B', rider=self.user)
        response = self.client.get(trip.get_absolute_url())
        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(TripSerializer(trip).data, response.data)


class WebSocketTripTest(ChannelTestCase):
    def setUp(self):
        self.driver = create_user(username='driver@example.com', group='driver')
        self.rider = create_user(username='rider@example.com', group='rider')
```

After modifications, all tests should pass.

```bash
$ python manage.py test trip.tests
```





## Rider Commands

```bash
$ curl -H "Content-Type: application/json" -X POST -d '{"username": "rider@example.com", "password1": "pAssw0rd!", "password2": "pAssw0rd!", "group": "rider"}' http://localhost:8000/api/sign_up/

{"id":1,"username":"rider@example.com","auth_token":null,"groups":["rider"]}
```

```bash
$ curl -H "Content-Type: application/json" -X POST -d '{"username": "rider@example.com", "password": "pAssw0rd!"}' http://localhost:8000/api/log_in/

{"id":1,"username":"rider@example.com","auth_token":81ff6ef21b02f22435d9b97f06e4c36b3bc4bb81,"groups":["rider"]}
```

```bash
$ curl -H "Authorization: Token 81ff6ef21b02f22435d9b97f06e4c36b3bc4bb81" -X POST http://localhost:8000/api/log_out/
```

```bash
$ wscat -H "Content-Type: application/json; Authorization: Token 81ff6ef21b02f22435d9b97f06e4c36b3bc4bb81" -c ws://localhost:8000/rider/ --parsecommands
```

```bash
> send '{"text":{"pick_up_address":"A","drop_off_address":"B","rider":{"id":3,"username":"rider@example.com"}}}'
```

## Driver Commands

```bash
$ curl -H "Content-Type: application/json" -X POST -d '{"username": "driver@example.com", "password1": "pAssw0rd!", "password2": "pAssw0rd!", "group": "driver"}' http://localhost:8000/api/sign_up/

{"id":1,"username":"driver@example.com","auth_token":null,"groups":["driver"]}
```

```bash
$ curl -H "Content-Type: application/json" -X POST -d '{"username": "driver@example.com", "password": "pAssw0rd!"}' http://localhost:8000/api/log_in/

{"id":1,"username":"driver@example.com","auth_token":43841bb28794f6b433b5c95df9ff879d104a2b6f,"groups":["driver"]}
```

```bash
$ curl -H "Authorization: Token 43841bb28794f6b433b5c95df9ff879d104a2b6f" -X POST http://localhost:8000/api/log_out/
```

## Universal Commands

```bash
$ curl -H "Authorization: Token 81ff6ef21b02f22435d9b97f06e4c36b3bc4bb81" http://localhost:8000/api/trip/

[]
```

```bash
$ curl -H "Authorization: Token 81ff6ef21b02f22435d9b97f06e4c36b3bc4bb81" http://localhost:8000/api/trip/something/

[]
```
