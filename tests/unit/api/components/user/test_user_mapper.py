import types

import pytest
from tests.factories.user_factory import UserFactory

from api.components.user.user_mapper import UserMapper
from api.components.user.user_models import User, UserResponse
from api.utils.dict_to_obj import DictToObj


class TestUserMapper:
    @pytest.fixture
    def user_mapper(self) -> UserMapper:
        return UserMapper()


class TestToPersistence(TestUserMapper):
    def test_should_define_a_function(
        self,
        user_mapper: UserMapper,
    ) -> None:
        assert isinstance(user_mapper.to_persistence, types.FunctionType) is True

    def test_should_succeed_and_return_a_raw_user_data(
        self,
        user_mapper: UserMapper,
    ) -> None:
        mocked_user: User = UserMapper.to_domain(UserFactory.build())
        expected_result = {"name": mocked_user.name, "email": mocked_user.email}

        result = user_mapper.to_persistence(mocked_user)

        assert result == expected_result


class TestToDomain(TestUserMapper):
    def test_should_define_a_function(
        self,
        user_mapper: UserMapper,
    ) -> None:
        assert isinstance(user_mapper.to_domain, types.FunctionType) is True

    def test_should_succeed_and_return_a_user_from_domain(
        self,
        user_mapper: UserMapper,
    ) -> None:
        mocked_user: User = UserMapper.to_domain(UserFactory.build())
        raw_user_data = {
            "id": mocked_user.id,
            "name": mocked_user.name,
            "email": mocked_user.email,
            "created_at": mocked_user.created_at,
            "updated_at": mocked_user.updated_at,
        }
        obj = DictToObj(raw_user_data)
        expected_result = mocked_user

        result = user_mapper.to_domain(obj)

        assert result.id == expected_result.id
        assert result.name == expected_result.name
        assert result.email == expected_result.email
        assert result.created_at == expected_result.created_at
        assert result.updated_at == expected_result.updated_at


class TestToResponse(TestUserMapper):
    def test_should_define_a_function(
        self,
        user_mapper: UserMapper,
    ) -> None:
        assert isinstance(user_mapper.to_response, types.FunctionType) is True

    def test_should_succeed_and_return_a_user_response(
        self,
        user_mapper: UserMapper,
    ) -> None:
        mocked_user: User = UserMapper.to_domain(UserFactory.build())
        expected_result = UserResponse(
            id=mocked_user.id,
            name=mocked_user.name,
            email=mocked_user.email,
            created_at=mocked_user.created_at,
            updated_at=mocked_user.updated_at,
        )

        result = user_mapper.to_response(mocked_user)

        assert result.id == expected_result.id
        assert result.name == expected_result.name
        assert result.email == expected_result.email
        assert result.created_at == expected_result.created_at
        assert result.updated_at == expected_result.updated_at
