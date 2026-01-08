"""
Test Data Generators.

This demonstrates the test data generation utilities I built
for creating realistic, consistent test data.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, TypeVar, Generic
from faker import Faker
import random
import string


fake = Faker()
T = TypeVar("T")


@dataclass
class User:
    """User data model."""
    id: str
    email: str
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Product:
    """Product data model."""
    id: str
    name: str
    price: float
    category: str
    description: Optional[str] = None
    in_stock: bool = True


@dataclass
class Order:
    """Order data model."""
    id: str
    user_id: str
    products: list[str]
    total: float
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)


class DataBuilder(Generic[T]):
    """
    Generic builder pattern for test data.

    Allows fluent construction of test objects
    with sensible defaults and customization.
    """

    def __init__(self, factory_func):
        self._factory = factory_func
        self._overrides = {}

    def with_field(self, field_name: str, value) -> "DataBuilder[T]":
        """Override a specific field."""
        self._overrides[field_name] = value
        return self

    def build(self) -> T:
        """Build the object with applied overrides."""
        return self._factory(**self._overrides)

    def build_many(self, count: int) -> list[T]:
        """Build multiple objects."""
        return [self._factory(**self._overrides) for _ in range(count)]


class UserFactory:
    """Factory for generating User test data."""

    @staticmethod
    def create(**overrides) -> User:
        """Create a user with random data."""
        defaults = {
            "id": f"user_{fake.uuid4()[:8]}",
            "email": fake.email(),
            "name": fake.name(),
            "phone": fake.phone_number(),
            "address": fake.address(),
            "created_at": fake.date_time_this_year()
        }
        defaults.update(overrides)
        return User(**defaults)

    @classmethod
    def builder(cls) -> DataBuilder[User]:
        """Get a builder for fluent construction."""
        return DataBuilder(cls.create)

    @classmethod
    def create_batch(cls, count: int, **overrides) -> list[User]:
        """Create multiple users."""
        return [cls.create(**overrides) for _ in range(count)]

    @classmethod
    def create_admin(cls) -> User:
        """Create an admin user."""
        return cls.create(
            email=os.getenv("ADMIN_EMAIL", "admin@example.com"),
            name="Admin User"
        )

    @classmethod
    def create_with_valid_email(cls) -> User:
        """Create user with guaranteed valid email format."""
        return cls.create(email=f"test_{fake.uuid4()[:8]}@example.com")


class ProductFactory:
    """Factory for generating Product test data."""

    CATEGORIES = ["Electronics", "Clothing", "Books", "Home", "Sports"]

    @classmethod
    def create(cls, **overrides) -> Product:
        """Create a product with random data."""
        defaults = {
            "id": f"prod_{fake.uuid4()[:8]}",
            "name": fake.catch_phrase(),
            "price": round(random.uniform(9.99, 999.99), 2),
            "category": random.choice(cls.CATEGORIES),
            "description": fake.text(max_nb_chars=200),
            "in_stock": random.choice([True, True, True, False])  # 75% in stock
        }
        defaults.update(overrides)
        return Product(**defaults)

    @classmethod
    def builder(cls) -> DataBuilder[Product]:
        """Get a builder for fluent construction."""
        return DataBuilder(cls.create)

    @classmethod
    def create_out_of_stock(cls) -> Product:
        """Create an out of stock product."""
        return cls.create(in_stock=False)

    @classmethod
    def create_expensive(cls, min_price: float = 500) -> Product:
        """Create an expensive product."""
        return cls.create(price=round(random.uniform(min_price, 9999.99), 2))


class OrderFactory:
    """Factory for generating Order test data."""

    STATUSES = ["pending", "confirmed", "shipped", "delivered", "cancelled"]

    @classmethod
    def create(cls, **overrides) -> Order:
        """Create an order with random data."""
        product_count = random.randint(1, 5)
        products = [f"prod_{fake.uuid4()[:8]}" for _ in range(product_count)]

        defaults = {
            "id": f"order_{fake.uuid4()[:8]}",
            "user_id": f"user_{fake.uuid4()[:8]}",
            "products": products,
            "total": round(random.uniform(29.99, 499.99), 2),
            "status": random.choice(cls.STATUSES),
            "created_at": fake.date_time_this_month()
        }
        defaults.update(overrides)
        return Order(**defaults)

    @classmethod
    def builder(cls) -> DataBuilder[Order]:
        """Get a builder for fluent construction."""
        return DataBuilder(cls.create)

    @classmethod
    def create_for_user(cls, user_id: str) -> Order:
        """Create an order for specific user."""
        return cls.create(user_id=user_id)


# Utility functions for common data patterns

def generate_unique_email() -> str:
    """Generate a unique email address."""
    return f"test_{fake.uuid4()[:8]}@example.com"


def generate_strong_password() -> str:
    """Generate a strong password meeting common requirements."""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    password = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
        random.choice("!@#$%^&*"),
    ]
    password.extend(random.choices(chars, k=8))
    random.shuffle(password)
    return "".join(password)


def generate_phone_number(country_code: str = "+1") -> str:
    """Generate a formatted phone number."""
    return f"{country_code} {fake.msisdn()[3:]}"


def generate_date_range(days_back: int = 30) -> tuple[datetime, datetime]:
    """Generate a date range for filtering."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    return start_date, end_date


# Example usage
if __name__ == "__main__":
    # Using factory directly
    user = UserFactory.create()
    print(f"Created user: {user.name} ({user.email})")

    # Using builder pattern
    product = (
        ProductFactory.builder()
        .with_field("name", "Test Product")
        .with_field("price", 99.99)
        .with_field("category", "Electronics")
        .build()
    )
    print(f"Created product: {product.name} - ${product.price}")

    # Creating batch
    users = UserFactory.create_batch(5)
    print(f"Created {len(users)} users")
