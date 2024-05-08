from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.mixins import (
    ListModelMixin,
    CreateModelMixin,
    DestroyModelMixin,
)
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from base.code_text import (REACTION_ALREADY_SET, SUCCESSFUL_RATED_IT, \
                            SUCCESSFUL_LIKED_THE_RECIPE, REACTION_CANCELLED,
                            ALREADY_RATED_THIS_COMMENT, SUCCESSFUL_RATED_COMMENT)
from src.base.throttling import ScopedOnePerThreeSecsThrottle
from src.apps.reactions.models import Reaction
from src.apps.reactions.serializers import (
    RecipeReactionsListSerializer,
    ReactionCreateSerializer,
    CommentReactionsListSerializer,
)

from src.apps.comments.models import Comment
from src.apps.recipes.models import Recipe


class ReactionViewSet(
    GenericViewSet, ListModelMixin, CreateModelMixin, DestroyModelMixin
):
    """Base class for getting, creating and deleting reactions."""

    serializer_class = RecipeReactionsListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    throttle_classes = [ScopedOnePerThreeSecsThrottle]
    throttle_scope = "reactions"
    swagger_tags = ["Reactions"]

    def get_queryset(self):
        path = self.request.path
        if "recipe" in path:
            return Recipe.objects.filter(slug=self.kwargs.get("slug"))
        elif "comment" in path:
            return Comment.objects.filter(id=self.kwargs.get("id"))
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def get_object(self):
        queryset = self.get_queryset()
        filter_field = self.kwargs
        obj = get_object_or_404(queryset, **filter_field)
        self.check_object_permissions(self.request, obj)
        return obj

    def get_serializer_class(self):
        if self.request.method == "GET":
            if "recipe" in self.request.path:
                self.serializer_class = RecipeReactionsListSerializer
            elif "comment" in self.request.path:
                self.serializer_class = CommentReactionsListSerializer
        if self.request.method == "POST":
            self.serializer_class = ReactionCreateSerializer
        return super().get_serializer_class()

    def list(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer_class()
        serializer = serializer(instance, context={"request": request})
        return Response(serializer.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        content_type = ContentType.objects.get_for_model(instance)
        serializer = self.get_serializer_class()
        serializer = serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        reaction, created = Reaction.objects.get_or_create(
            emoji=serializer.data["emoji"],
            author=self.request.user,
            object_id=instance.id,
            content_type=content_type,
        )

        if not created and not reaction.is_deleted:
            return Response(
                REACTION_ALREADY_SET,
                status=status.HTTP_403_FORBIDDEN,
            )
        if reaction.is_deleted:
            reaction.is_deleted = False
            reaction.save()

        return Response(
            SUCCESSFUL_RATED_IT, status=status.HTTP_201_CREATED
        )


class RecipeReactionViewSet(ReactionViewSet):
    """Subclass for creating and deleting reactions on recipes"""

    def create(self, request, *args, **kwargs):
        """Create a reaction on recipe"""
        response = super().create(self, request, *args, **kwargs)
        if response.status_code == status.HTTP_403_FORBIDDEN:
            return Response(
                REACTION_ALREADY_SET,
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            SUCCESSFUL_LIKED_THE_RECIPE, status=status.HTTP_201_CREATED
        )

    def destroy(self, request, *args, **kwargs):
        reaction = get_object_or_404(
            Reaction,
            id=kwargs.get("pk"),
            recipe_reactions__slug=kwargs.get("slug"),
            author=request.user,
        )
        reaction.is_deleted = True
        reaction.save()
        return Response(
            REACTION_CANCELLED, status=status.HTTP_204_NO_CONTENT
        )


class CommentReactionViewSet(ReactionViewSet):
    """Subclass creating and deleting reactions on comment"""

    def create(self, request, *args, **kwargs):
        response = super().create(self, request, *args, **kwargs)
        if response.status_code == status.HTTP_403_FORBIDDEN:
            return Response(
                ALREADY_RATED_THIS_COMMENT,
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            SUCCESSFUL_RATED_COMMENT, status=status.HTTP_201_CREATED
        )

    def destroy(self, request, *args, **kwargs):
        reaction = get_object_or_404(
            Reaction,
            id=kwargs.get("pk"),
            comment_reactions__id=kwargs.get("id"),
            author=request.user,
        )
        reaction.is_deleted = True
        reaction.save()
        return Response(
            REACTION_CANCELLED, status=status.HTTP_204_NO_CONTENT
        )
