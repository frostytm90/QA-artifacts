import pytest
import os
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from api_client import UserServiceClient


# Load test password from environment - never hardcode credentials
TEST_PASSWORD = os.getenv("TEST_USER_PASSWORD", "")


# response schemas
class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        extra = "forbid"


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int
    page: int
    limit: int


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None


# fixtures

@pytest.fixture
def user_client(api_base_url):
    return UserServiceClient(api_base_url)


@pytest.fixture
def auth_client(user_client, test_creds):
    user_client.login(test_creds["email"], test_creds["password"])
    return user_client


@pytest.fixture
def created_user(auth_client, faker):
    """create user for test, delete after"""
    resp = auth_client.create_user(
        email=faker.email(),
        name=faker.name(),
        password=TEST_PASSWORD
    )

    user = resp.json_data
    yield user

    # cleanup
    auth_client.delete_user(user["id"])


# tests

class TestCreateUser:

    def test_create_user_success(self, auth_client, faker):
        email = faker.email()
        name = faker.name()

        resp = auth_client.create_user(
            email=email,
            name=name,
            password=TEST_PASSWORD
        )

        assert resp.status_code == 201

        # validate schema
        user = UserResponse(**resp.json_data)
        assert user.email == email
        assert user.name == name

        # cleanup
        auth_client.delete_user(user.id)

    @pytest.mark.parametrize("bad_email", [
        "not-an-email",
        "missing@domain",
        "@nodomain.com",
        "",
    ])
    def test_create_user_bad_email(self, auth_client, bad_email):
        resp = auth_client.create_user(
            email=bad_email,
            name="Test",
            password=TEST_PASSWORD
        )

        assert resp.status_code == 400
        err = ErrorResponse(**resp.json_data)
        assert "email" in err.message.lower()

    def test_create_user_duplicate_email(self, auth_client, created_user):
        resp = auth_client.create_user(
            email=created_user["email"],
            name="Another User",
            password=TEST_PASSWORD
        )

        assert resp.status_code == 409


class TestGetUser:

    def test_get_user_success(self, auth_client, created_user):
        resp = auth_client.get_user(created_user["id"])

        assert resp.status_code == 200
        user = UserResponse(**resp.json_data)
        assert user.id == created_user["id"]

    def test_get_user_not_found(self, auth_client):
        resp = auth_client.get_user("nonexistent-id-123")

        assert resp.status_code == 404

    def test_get_user_no_auth(self, user_client, created_user):
        # client without token
        resp = user_client.get_user(created_user["id"])

        assert resp.status_code == 401


class TestListUsers:

    def test_list_users_pagination(self, auth_client):
        resp = auth_client.list_users(page=1, limit=10)

        assert resp.status_code == 200
        data = UserListResponse(**resp.json_data)
        assert data.page == 1
        assert data.limit == 10
        assert len(data.users) <= 10


class TestUpdateUser:

    def test_update_name(self, auth_client, created_user):
        new_name = "Updated Name"

        resp = auth_client.update_user(created_user["id"], name=new_name)

        assert resp.status_code == 200
        user = UserResponse(**resp.json_data)
        assert user.name == new_name


class TestDeleteUser:

    def test_delete_user(self, auth_client, faker):
        # create then delete
        create_resp = auth_client.create_user(
            email=faker.email(),
            name=faker.name(),
            password=TEST_PASSWORD
        )
        user_id = create_resp.json_data["id"]

        del_resp = auth_client.delete_user(user_id)
        assert del_resp.status_code == 204

        # verify gone
        get_resp = auth_client.get_user(user_id)
        assert get_resp.status_code == 404
