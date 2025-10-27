"""
Custom pagination classes for the application.
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _


class StandardResultsSetPagination(PageNumberPagination):
    """
    A standard page number pagination style.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data
        })


class LargeResultsSetPagination(StandardResultsSetPagination):
    """
    A pagination class for large result sets.
    """
    page_size = 50
    max_page_size = 500


class SmallResultsSetPagination(StandardResultsSetPagination):
    """
    A pagination class for small result sets.
    """
    page_size = 10
    max_page_size = 50


class CursorPagination(PageNumberPagination):
    """
    A cursor-based pagination class.
    """
    cursor_query_param = 'cursor'
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    ordering = '-created_at'
    
    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'results': data
        })
