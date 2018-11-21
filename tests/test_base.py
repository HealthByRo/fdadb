from django.contrib.auth import get_user_model
from tests.test_utils import BaseTestCase

UserModel = get_user_model()


class TestPlaceholder(BaseTestCase):
    def test_user_create(self):
        self.assertTrue(True)
