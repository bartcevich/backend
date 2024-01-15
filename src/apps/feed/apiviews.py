from src.apps.recipes.models import Recipe
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import OrderingFilter
from rest_framework import generics, viewsets, filters, mixins
from .serializers import FeedSerializer
from django.db.models import Sum, Count, F


class FeedSubscriptionsPagination(PageNumberPagination):
    page_size = 5


class FeedUserPagination(PageNumberPagination):
    page_size = 5


class FeedPopularPagination(PageNumberPagination):
    page_size = 5


class FeedSubscriptionsList(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Listing all posts of authors user subscribed to sorted by pub date
    """

    pagination_class = FeedSubscriptionsPagination
    serializer_class = FeedSerializer

    def get_queryset(self):
        user = self.request.user
        users_subscribed_to = user.following.all().values_list("user_id", flat=True)
        queryset = (
            Recipe.objects.filter(author__in=users_subscribed_to)
            .order_by("-pub_date")
            .annotate(
                comments_count=Count("comments"),
                views_count=Count("views"),
                reactions_count=Count("reactions"),
                activity_count=F("comments_count")
                + F("views_count")
                + F("reactions_count"),
            )
        )

        return queryset


class FeedUserList(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Listing all created user's posts with pagination and sorting by pub_date
    """

    serializer_class = FeedSerializer
    pagination_class = FeedUserPagination

    def get_queryset(self):
        user = self.request.user
        queryset = (
            Recipe.objects.filter(author=user)
            .order_by("-pub_date")
            .annotate(
                comments_count=Count("comments"),
                views_count=Count("views"),
                reactions_count=Count("reactions"),
                activity_count=F("comments_count")
                + F("views_count")
                + F("reactions_count"),
            )
        )

        return queryset


class FeedPopularList(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Listing all popular posts with additional sort by pub_date
    """

    queryset = Recipe.objects.annotate(
        comments_count=Count("comments"),
        views_count=Count("views"),
        reactions_count=Count("reactions"),
        activity_count=F("comments_count") + F("views_count") + F("reactions_count"),
    )
    pagination_class = FeedPopularPagination
    serializer_class = FeedSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["pub_date"]
    ordering = ["-activity_count"]
