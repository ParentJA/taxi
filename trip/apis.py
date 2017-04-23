# Django imports.
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import Group

# Third-party imports.
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView

# Local imports.
from .models import Trip
from .permissions import IsDriver
from .serializers import TripSerializer, UserSerializer, PrivateUserSerializer


class SignUpView(APIView):
    permission_classes = (AllowAny,)

    def post(self, *args, **kwargs):
        group = self.request.data.get('group', 'rider')
        user_group, _ = Group.objects.get_or_create(name=group)
        form = UserCreationForm(data=self.request.data)
        if form.is_valid():
            user = form.save()
            user.email = self.request.data.get('email')
            user.groups.add(user_group)
            user.save()
            return Response(status=HTTP_201_CREATED, data=PrivateUserSerializer(user).data)
        else:
            return Response(status=HTTP_400_BAD_REQUEST, data=form.errors)


class LogInView(APIView):
    permission_classes = (AllowAny,)

    def post(self, *args, **kwargs):
        form = AuthenticationForm(data=self.request.data)
        if form.is_valid():
            user = form.get_user()
            login(self.request, user)
            Token.objects.get_or_create(user=user)
            return Response(status=HTTP_200_OK, data=PrivateUserSerializer(user).data)
        else:
            return Response(status=HTTP_400_BAD_REQUEST, data=form.errors)


class LogOutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, *args, **kwargs):
        Token.objects.get(user=self.request.user).delete()
        logout(self.request)
        return Response(status=HTTP_204_NO_CONTENT)


class UserListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_queryset(self):
        return get_user_model().objects.exclude(username=self.request.user.username)


class TripView(RetrieveModelMixin, UpdateModelMixin, ListCreateAPIView):
    """
    Home:
    
    Trip:
    
    Past:
    """

    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('status',)
    lookup_field = 'nk'
    lookup_url_kwarg = 'trip_nk'
    permission_classes = (IsAuthenticated,)
    queryset = Trip.objects.all()
    serializer_class = TripSerializer

    # def perform_create(self, serializer):
    #     trip = serializer.save()
    #     driver = self.request.data.get('driver')
    #     if driver:
    #         driver.pop('groups')
    #         trip.driver = get_user_model().objects.get(**driver)
    #     trip.riders.add(self.request.user)
    #     for rider in self.request.data.get('riders', []):
    #         rider.pop('groups')
    #         trip.riders.add(get_user_model().objects.get(**rider))
    #     trip.save()
    #
    # def perform_update(self, serializer):
    #     trip = serializer.save()
    #     driver = self.request.data.get('driver')
    #     if driver:
    #         driver.pop('groups')
    #         trip.driver = get_user_model().objects.get(**driver)
    #     trip.riders.add(self.request.user)
    #     for rider in self.request.data.get('riders', []):
    #         rider.pop('groups')
    #         trip.riders.add(get_user_model().objects.get(**rider))
    #     trip.save()

    def put(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class TripStatusView(RetrieveUpdateAPIView):
    lookup_field = 'nk'
    lookup_url_kwarg = 'trip_nk'
    permission_classes = (IsDriver,)
    queryset = Trip.objects.all()
    serializer_class = TripSerializer

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        status = request.data.get('status')

        # Driver accepted trip and is en route to pick up address.
        if status == Trip.STARTED:
            return response

        # Driver has picked up rider(s) and is en route to drop off address.
        if status == Trip.IN_PROGRESS:
            return response

        # Driver has dropped off rider(s).
        if status == Trip.COMPLETED:
            return response

        # TODO: Do channel stuff...
