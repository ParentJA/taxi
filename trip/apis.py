# Django imports.
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import Group

# Third-party imports.
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

# Local imports.
from .models import Trip
from .serializers import TripSerializer, PrivateUserSerializer


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


class TripView(ReadOnlyModelViewSet):
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('status',)
    lookup_field = 'nk'
    lookup_url_kwarg = 'trip_nk'
    permission_classes = (IsAuthenticated,)
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
