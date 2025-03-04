from db.models.user import UserModel
from factory import BUILD_STRATEGY, Factory, LazyAttribute
from faker import Faker

faker = Faker()


class UserFactory(Factory):
    class Meta:
        strategy = BUILD_STRATEGY
        model = UserModel

    id = LazyAttribute(lambda _: faker.uuid4())
    name = LazyAttribute(lambda _: faker.user_name())
    email = LazyAttribute(lambda _: faker.email())
    created_at = LazyAttribute(lambda _: faker.date_time())
    updated_at = LazyAttribute(lambda _: faker.date_time())
