"""Тесты модели пользователя, входящего по email."""

import pytest
from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError
from django.urls import reverse

User = get_user_model()
pytestmark = pytest.mark.django_db


class TestUserModel:
    def test_username_field_is_email(self):
        assert User.USERNAME_FIELD == "email"
        assert User.REQUIRED_FIELDS == []

    def test_model_has_no_username_field(self):
        assert "username" not in {f.name for f in User._meta.get_fields()}

    def test_create_user(self):
        user = User.objects.create_user(email="user@example.com", password="pass12345")

        assert user.email == "user@example.com"
        assert user.check_password("pass12345")
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email="admin@example.com", password="pass12345"
        )

        assert admin.is_staff
        assert admin.is_superuser
        assert admin.is_active

    def test_email_is_normalized(self):
        """Домен приводится к нижнему регистру — иначе появятся дубли-близнецы."""
        user = User.objects.create_user(email="User@EXAMPLE.COM", password="pass12345")

        assert user.email == "User@example.com"

    def test_email_is_unique(self):
        User.objects.create_user(email="user@example.com", password="pass12345")

        with pytest.raises(IntegrityError):
            User.objects.create_user(email="user@example.com", password="other12345")

    def test_email_is_required(self):
        with pytest.raises(ValueError):
            User.objects.create_user(email="", password="pass12345")

    def test_superuser_flags_cannot_be_overridden(self):
        with pytest.raises(ValueError):
            User.objects.create_superuser(
                email="fake@example.com", password="pass12345", is_superuser=False
            )

    def test_str_is_email(self):
        user = User.objects.create_user(email="user@example.com", password="pass12345")

        assert str(user) == "user@example.com"


class TestAuthentication:
    def test_login_by_email(self):
        User.objects.create_user(email="user@example.com", password="pass12345")

        assert (
            authenticate(username="user@example.com", password="pass12345") is not None
        )

    def test_wrong_password_rejected(self):
        User.objects.create_user(email="user@example.com", password="pass12345")

        assert authenticate(username="user@example.com", password="wrong") is None


class TestAdminIntegration:
    """Админка использует нестандартные формы — проверяем, что они собираются."""

    @pytest.fixture
    def admin_client(self, client):
        User.objects.create_superuser(email="admin@example.com", password="pass12345")
        client.login(username="admin@example.com", password="pass12345")
        return client

    def test_user_list_page(self, admin_client):
        response = admin_client.get(reverse("admin:users_user_changelist"))

        assert response.status_code == 200

    def test_user_add_page(self, admin_client):
        response = admin_client.get(reverse("admin:users_user_add"))

        assert response.status_code == 200

    def test_user_change_page(self, admin_client):
        user = User.objects.create_user(email="user@example.com", password="pass12345")

        response = admin_client.get(reverse("admin:users_user_change", args=[user.pk]))

        assert response.status_code == 200

    def test_create_user_through_admin(self, admin_client):
        response = admin_client.post(
            reverse("admin:users_user_add"),
            {
                "email": "new@example.com",
                "password1": "SuperSecret123",
                "password2": "SuperSecret123",
            },
        )

        assert response.status_code == 302
        assert User.objects.filter(email="new@example.com").exists()

    def test_catalog_admin_still_works(self, admin_client):
        response = admin_client.get(reverse("admin:catalog_album_changelist"))

        assert response.status_code == 200
