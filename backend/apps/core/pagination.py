from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsPagination(PageNumberPagination):
    """
    Standard pagination: 20 items per page, configurable via query param.
    Returns metadata alongside results.
    """
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 200
    page_query_param = "page"

    def get_paginated_response(self, data):
        return Response({
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "total_pages": self.page.paginator.num_pages,
            "current_page": self.page.number,
            "results": data,
        })

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "required": ["count", "results"],
            "properties": {
                "count": {"type": "integer", "description": "Total number of items"},
                "next": {"type": "string", "nullable": True, "description": "URL for next page"},
                "previous": {"type": "string", "nullable": True, "description": "URL for previous page"},
                "total_pages": {"type": "integer"},
                "current_page": {"type": "integer"},
                "results": schema,
            },
        }
