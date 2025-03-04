import re
import types

import pytest
from tests.factories.user_factory import UserFactory

from api.components.user.user_mapper import UserMapper
from api.shared.api_pagination_response import APIPaginationResponse
from services.api_pagination_service import APIPaginationData, APIPaginationService


class TestAPIPaginationService:
    @pytest.fixture
    def base_url(self) -> str:
        return "http://localhost:5002/users"

    @pytest.fixture
    def api_pagination_service(self) -> APIPaginationService:
        return APIPaginationService()


class TestCreateResponse(TestAPIPaginationService):
    def test_should_define_a_method(
        self,
        api_pagination_service: APIPaginationService,
    ) -> None:
        assert (
            isinstance(api_pagination_service.create_response, types.MethodType) is True
        )

    def test_should_succeed_and_return_a_response_when_there_are_no_records(
        self,
        base_url: str,
        api_pagination_service: APIPaginationService,
    ) -> None:
        page = 1
        limit = 1
        total_pages = 0
        total_records = 0
        records = []
        api_pagination_data = APIPaginationData(
            page=page, limit=limit, total_records=total_records, records=records
        )
        expected_result = APIPaginationResponse(
            page=api_pagination_data.page,
            limit=api_pagination_data.limit,
            total_pages=total_pages,
            total_records=total_records,
            records=records,
            previous=None,
            next=None,
        )

        result = api_pagination_service.create_response(base_url, api_pagination_data)

        assert result == expected_result

    def test_should_succeed_and_return_a_response_when_previous_page_is_completely_filled_with_all_records(
        self,
        base_url: str,
        api_pagination_service: APIPaginationService,
    ) -> None:
        base_url = f"{base_url}?page=2"
        page = 2
        limit = 1
        total_pages = 1
        total_records = 1
        records = []
        api_pagination_data = APIPaginationData(
            page=page, limit=limit, total_records=total_records, records=records
        )
        expected_result = APIPaginationResponse(
            page=api_pagination_data.page,
            limit=api_pagination_data.limit,
            total_pages=total_pages,
            total_records=total_records,
            records=records,
            previous=None,
            next=None,
        )

        result = api_pagination_service.create_response(base_url, api_pagination_data)

        assert result == expected_result

    def test_should_succeed_and_return_a_response_when_previous_page_is_not_completely_filled_with_all_records(
        self,
        base_url: str,
        api_pagination_service: APIPaginationService,
    ) -> None:
        base_url = f"{base_url}?page=2&limit=2"
        page = 2
        limit = 2
        total_pages = 1
        total_records = 1
        records = []
        api_pagination_data = APIPaginationData(
            page=page, limit=limit, total_records=total_records, records=records
        )
        expected_result = APIPaginationResponse(
            page=api_pagination_data.page,
            limit=api_pagination_data.limit,
            total_pages=total_pages,
            total_records=total_records,
            records=records,
            previous=None,
            next=None,
        )

        result = api_pagination_service.create_response(base_url, api_pagination_data)

        assert result == expected_result

    def test_should_succeed_and_return_a_response_when_previous_page_is_completely_filled_and_there_are_still_records_left(
        self,
        base_url: str,
        api_pagination_service: APIPaginationService,
    ) -> None:
        base_url = f"{base_url}?page=2"
        page = 2
        limit = 1
        total_pages = 2
        total_records = 2
        count = 1
        records = [UserMapper.to_response(u) for u in UserFactory.build_batch(count)]
        api_pagination_data = APIPaginationData(
            page=page, limit=limit, total_records=total_records, records=records
        )
        previous = re.sub(r"(page=)[^&]", rf"\g<1>{page-1}", base_url)
        expected_result = APIPaginationResponse(
            page=api_pagination_data.page,
            limit=api_pagination_data.limit,
            total_pages=total_pages,
            total_records=total_records,
            records=records,
            previous=previous,
            next=None,
        )

        result = api_pagination_service.create_response(base_url, api_pagination_data)

        assert result == expected_result

    def test_should_succeed_and_return_a_response_when_current_page_is_completely_filled_with_all_records(
        self,
        base_url: str,
        api_pagination_service: APIPaginationService,
    ) -> None:
        base_url = f"{base_url}?page=3"
        page = 3
        limit = 1
        total_pages = 3
        total_records = 3
        count = 1
        records = [UserMapper.to_response(u) for u in UserFactory.build_batch(count)]
        api_pagination_data = APIPaginationData(
            page=page, limit=limit, total_records=total_records, records=records
        )
        previous = re.sub(r"(page=)[^&]", rf"\g<1>{page-1}", base_url)
        expected_result = APIPaginationResponse(
            page=api_pagination_data.page,
            limit=api_pagination_data.limit,
            total_pages=total_pages,
            total_records=total_records,
            records=records,
            previous=previous,
            next=None,
        )

        result = api_pagination_service.create_response(base_url, api_pagination_data)

        assert result == expected_result

    def test_should_succeed_and_return_a_response_when_only_page_query_param_is_sent_in_request_url(
        self,
        base_url: str,
        api_pagination_service: APIPaginationService,
    ) -> None:
        base_url = f"{base_url}?page=1"
        page = 1
        limit = 1
        total_pages = 2
        total_records = 2
        count = 1
        records = [UserMapper.to_response(u) for u in UserFactory.build_batch(count)]
        api_pagination_data = APIPaginationData(
            page=page, limit=limit, total_records=total_records, records=records
        )
        next = re.sub(r"(page=)[^&]", rf"\g<1>{page+1}", base_url)
        expected_result = APIPaginationResponse(
            page=api_pagination_data.page,
            limit=api_pagination_data.limit,
            total_pages=total_pages,
            total_records=total_records,
            records=records,
            previous=None,
            next=next,
        )

        result = api_pagination_service.create_response(base_url, api_pagination_data)

        assert result == expected_result

    def test_should_succeed_and_return_a_response_when_only_limit_query_param_is_sent_in_request_url(
        self,
        base_url: str,
        api_pagination_service: APIPaginationService,
    ) -> None:
        base_url = f"{base_url}?limit=2"
        page = 1
        limit = 2
        total_pages = 2
        total_records = 4
        count = 2
        records = [UserMapper.to_response(u) for u in UserFactory.build_batch(count)]
        api_pagination_data = APIPaginationData(
            page=page, limit=limit, total_records=total_records, records=records
        )
        next = f"{base_url}&page={page + 1}"
        expected_result = APIPaginationResponse(
            page=api_pagination_data.page,
            limit=api_pagination_data.limit,
            total_pages=total_pages,
            total_records=total_records,
            records=records,
            previous=None,
            next=next,
        )

        result = api_pagination_service.create_response(base_url, api_pagination_data)

        assert result == expected_result

    def test_should_succeed_and_return_a_response_when_neither_page_nor_limit_query_params_are_sent_in_request_url(
        self,
        base_url: str,
        api_pagination_service: APIPaginationService,
    ) -> None:
        page = 1
        limit = 1
        total_pages = 2
        total_records = 2
        count = 1
        records = [UserMapper.to_response(u) for u in UserFactory.build_batch(count)]
        api_pagination_data = APIPaginationData(
            page=page, limit=limit, total_records=total_records, records=records
        )
        next = f"{base_url}?page={page + 1}&limit={limit}"
        expected_result = APIPaginationResponse(
            page=api_pagination_data.page,
            limit=api_pagination_data.limit,
            total_pages=total_pages,
            total_records=total_records,
            records=records,
            previous=None,
            next=next,
        )

        result = api_pagination_service.create_response(base_url, api_pagination_data)

        assert result == expected_result
