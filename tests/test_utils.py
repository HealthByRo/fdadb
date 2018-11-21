from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

UserModel = get_user_model()


class BaseTestCase(APITestCase):
    pass
