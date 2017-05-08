from django.contrib.auth import get_user_model
from channels import Group
from channels.test import ChannelTestCase, HttpClient
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT
from rest_framework.test import APIClient, APITestCase
from .models import Trip
from .serializers import PublicUserSerializer, PrivateUserSerializer, TripSerializer

PASSWORD = 'pAssw0rd!'


def create_user(username='user@example.com', password=PASSWORD):
    return get_user_model().objects.create_user(username=username, password=password)


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
        self.client.login(username=user.username, password=PASSWORD)
        response = self.client.post(reverse('log_out'))
        self.assertEqual(HTTP_204_NO_CONTENT, response.status_code)
        self.assertFalse(Token.objects.filter(user=user).exists())


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

    def test_user_can_retrieve_trip_by_nk(self):
        trip = Trip.objects.create(pick_up_address='A', drop_off_address='B')
        response = self.client.get(trip.get_absolute_url())
        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(TripSerializer(trip).data, response.data)


class WebSocketTripTest(ChannelTestCase):
    def setUp(self):
        self.driver = create_user(username='driver@example.com')
        self.rider = create_user(username='rider@example.com')

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

    def update_trip(self, driver, trip, status):
        client = self.connect_as_driver(driver)
        client.send_and_consume('websocket.receive', path='/driver/', content={
            'text': {
                'nk': trip.nk,
                'pick_up_address': trip.pick_up_address,
                'drop_off_address': trip.drop_off_address,
                'status': status,
                'driver': PublicUserSerializer(driver).data
            }
        })
        return client

    def test_driver_can_connect_via_websockets(self):
        client = HttpClient()
        client.login(username=self.driver.username, password='pAssw0rd!')
        client.send_and_consume('websocket.connect', path='/driver/')
        message = client.receive()
        self.assertIsNone(message)

    def test_rider_can_connect_via_websockets(self):
        client = HttpClient()
        client.login(username=self.rider.username, password='pAssw0rd!')
        client.send_and_consume('websocket.connect', path='/rider/')
        message = client.receive()
        self.assertIsNone(message)

    def test_rider_can_create_trips(self):
        client = self.create_trip(self.rider)
        trip = Trip.objects.last()
        self.assertEqual(TripSerializer(trip).data, client.receive())

    def test_rider_is_subscribed_to_trip_channel(self):
        client = self.create_trip(self.rider)
        client.receive()
        trip = Trip.objects.last()
        message = {'message': 'test'}
        Group(trip.nk).send(message)
        self.assertEqual(message, client.receive())

    def test_rider_is_not_subscribed_to_other_trip_channel(self):
        trip = Trip.objects.create(pick_up_address='B', drop_off_address='C')
        client = self.create_trip(self.rider)
        client.receive()
        message = {'message': 'test'}
        Group(trip.nk).send(message)
        self.assertIsNone(client.receive())

    def test_driver_is_alerted_on_trip_creation(self):
        client = self.connect_as_driver(self.driver)
        self.create_trip(self.rider)
        trip = Trip.objects.last()
        self.assertEqual(TripSerializer(trip).data, client.receive())

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

    def test_rider_is_alerted_on_trip_update(self):
        client = self.create_trip(self.rider)
        client.receive()
        trip = Trip.objects.last()
        self.update_trip(self.driver, trip=trip, status=Trip.STARTED)
        trip = Trip.objects.get(nk=trip.nk)
        self.assertEqual(TripSerializer(trip).data, client.receive())
