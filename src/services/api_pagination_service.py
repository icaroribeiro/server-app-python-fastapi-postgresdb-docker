import math
import re
from abc import ABC, abstractmethod

from pydantic import BaseModel

from api.shared.api_pagination_response import APIPaginationResponse, T


class APIPaginationData(BaseModel):
    page: int
    limit: int
    total_records: int
    records: list[T]


class IAPIPaginationService(ABC):
    @abstractmethod
    def create_response(
        self, base_url: str, api_pagination_data: APIPaginationData
    ) -> APIPaginationResponse:
        raise Exception("NotImplementedException")


class APIPaginationService:
    def create_response(
        self, base_url: str, api_pagination_data: APIPaginationData
    ) -> APIPaginationResponse:
        return APIPaginationResponse(
            page=api_pagination_data.page,
            limit=api_pagination_data.limit,
            total_pages=self.__get_total_pages(
                api_pagination_data.limit,
                api_pagination_data.total_records,
            ),
            total_records=api_pagination_data.total_records,
            records=api_pagination_data.records,
            previous=self.__get_previous_page(
                base_url,
                api_pagination_data.page,
                api_pagination_data.limit,
                api_pagination_data.total_records,
            ),
            next=self.__get_next_page(
                base_url,
                api_pagination_data.page,
                api_pagination_data.limit,
                api_pagination_data.total_records,
            ),
        )

    @staticmethod
    def __get_total_pages(limit: int, total_records: int) -> int:
        return math.ceil(total_records / limit)

    @staticmethod
    def __get_previous_page(
        base_url: str, page: int, limit: int, total_records: int
    ) -> str | None:
        if page == 1:
            return None
        if total_records - (page - 1) * limit <= 0:
            return None
        return re.sub(r"(page=)[^&]", rf"\g<1>{page-1}", base_url)

    @staticmethod
    def __get_next_page(
        base_url: str, page: int, limit: int, total_records: int
    ) -> str | None:
        if total_records - page * limit <= 0:
            return None
        if "page" in base_url:
            return re.sub(r"(page=)[^&]", rf"\g<1>{page+1}", base_url)
        if "limit" in base_url:
            return base_url + f"&page={page + 1}"
        return base_url + f"?page={page + 1}&limit=1"
