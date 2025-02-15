from datetime import timedelta
from typing import List, Any, Set

from random import sample
from typing import Type

from django.contrib.contenttypes.models import ContentType
from rest_framework.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Model
from django.http import HttpRequest
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from unidecode import unidecode

from config.settings import SHORT_RECIPE_SYMBOLS, TIME_FROM_VIEW_RECIPE
from src.apps.ingredients.models import Ingredient, Unit, IngredientInRecipe
from src.base.code_text import (
    CANT_ADD_TWO_SIMILAR_INGREDIENT,
)


def validate_avatar_size(value: Any) -> None:
    """Validate avatar size"""

    if value.size > 5 * 1024 * 1024:  # 5 МБ в байтах
        raise ValidationError(
            _("Размер файла слишком большой. Максимальный размер - 5 МБ.")
        )


def user_avatar_path(instance: Model, filename: str) -> str:
    """Generate filepath for user avatar"""

    return f"avatar/user_{instance.id}/{filename}"


def recipe_preview_path(instance: Model, filename: str) -> str:
    """Generate filepath for recipe preview"""

    return f"preview/recipe_{instance.slug}/{filename}"


def shorten_text(full_text: str, n: int) -> str:
    """
    Shorten text to n characters with rounding by last word
    """

    short_text = full_text[:SHORT_RECIPE_SYMBOLS]
    if len(full_text) > n and full_text[n] != "":
        short_text = short_text[: short_text.rfind(" ")]
    return short_text


def bulk_get_or_create(
    model: Type[Model], objs: List[Model], match_field: str
) -> List[Model]:
    """
    Bulk get or create objects
    """

    match_values: List[Any] = [getattr(obj, match_field) for obj in objs]
    existing_objs: List[Model] = model.objects.filter(
        **{f"{match_field}__in": match_values}
    )

    existing_map: dict = {getattr(obj, match_field): obj for obj in existing_objs}

    objs_to_create: List[Model] = [
        obj for obj in objs if getattr(obj, match_field) not in existing_map
    ]

    created_objs: List[Model] = model.objects.bulk_create(objs_to_create)
    existing_map.update({getattr(obj, match_field): obj for obj in created_objs})
    return [existing_map[value] for value in match_values]


def create_ingredients_in_recipe(
    recipe: Model, ingredients_data: List[dict]
) -> List[Model]:
    """
    Create or update ingredients in recipe
    """

    ingredient_names: List[str] = [data["name"] for data in ingredients_data]
    if len(ingredient_names) != len(set(ingredient_names)):
        raise ValidationError(CANT_ADD_TWO_SIMILAR_INGREDIENT, code="unique_ingredient")

    existing_ingredients: List[IngredientInRecipe] = IngredientInRecipe.objects.filter(
        recipe=recipe
    )
    existing_ingredient_names: Set = set(
        existing_ingredients.values_list("ingredient__name", flat=True)
    )

    ingredients_to_remove: Set = existing_ingredient_names - set(ingredient_names)
    existing_ingredients.filter(ingredient__name__in=ingredients_to_remove).delete()

    existing_ingredients: List[str] = IngredientInRecipe.objects.filter(
        recipe=recipe, ingredient__name__in=ingredient_names
    ).values_list("ingredient__name", flat=True)

    new_ingredients: List[dict] = [
        data for data in ingredients_data if data["name"] not in existing_ingredients
    ]

    ingredient_objs: List[Ingredient] = [
        Ingredient(name=data["name"]) for data in new_ingredients
    ]
    unit_names: Set[str] = {data["unit"] for data in new_ingredients}
    unit_objs: List[Unit] = [Unit(name=name) for name in unit_names]

    with transaction.atomic():
        ingredients: dict = {
            ingredient.name: ingredient
            for ingredient in bulk_get_or_create(Ingredient, ingredient_objs, "name")
        }
        units: dict = {
            unit.name: unit for unit in bulk_get_or_create(Unit, unit_objs, "name")
        }

    ingredients_in_recipe_objs: List[IngredientInRecipe] = [
        IngredientInRecipe(
            recipe=recipe,
            ingredient=ingredients[ingredient_data["name"]],
            unit=units[ingredient_data["unit"]],
            amount=ingredient_data["amount"],
        )
        for ingredient_data in new_ingredients
    ]
    IngredientInRecipe.objects.bulk_create(ingredients_in_recipe_objs)
    return IngredientInRecipe.objects.filter(recipe=recipe)


def increment_view_count(
    model: Type[Model], recipe: Model, request: HttpRequest
) -> None:
    """Increment view count"""

    user_id: str = (
        request.user
        if request.user.is_authenticated
        else f"Anonymous-{request.META.get('REMOTE_ADDR')}"
    )
    time_threshold: timezone.datetime = timezone.now() - timedelta(
        minutes=TIME_FROM_VIEW_RECIPE
    )

    view_exists: bool = model.objects.filter(
        user=user_id, recipe=recipe, created_at__gte=time_threshold
    ).exists()

    if not view_exists:
        model.objects.create(user=user_id, recipe=recipe)


def create_recipe_slug(model: Type[Model], data: dict, num: int = 1) -> dict:
    """Create recipe slug"""

    with transaction.atomic():
        same_recipes: int = model.objects.filter(
            title__startswith=data["title"]
        ).count()
        slug_str: str = unidecode(
            f"{data['title']}_{same_recipes + num}" if same_recipes else data["title"]
        )
        data["slug"]: str = slugify(slug_str)

        if model.objects.filter(slug=data["slug"]).exists():
            num += 1
            create_recipe_slug(model, data, num)

    return data


def generate_username(user_id: int, model: Type[Model]) -> str:
    """
    Generate a unique username for a user.

    Args:
        user_id (int): The ID of the user.
        model (Type[CustomUser]): The CustomUser model class.

    Returns:
        str: A unique username for the user.
    """

    base_username: str = f"user{user_id}"

    if not model.objects.filter(username=base_username).exists():
        return base_username
    else:

        random_numbers = sample(range(100000, 1000000), 100)
        for random_number in random_numbers:
            new_username = f"user{random_number}"
            if not model.objects.filter(username=new_username).exists():
                return new_username

        return generate_username(user_id, model)


def count_reactions_on_objects(instance: Model) -> dict:
    """Count reactions made on an object by their emoji"""

    reactions_queryset = (
        instance.reactions.values("emoji")
        .filter(is_deleted=False)
        .annotate(count=Count("emoji"))
    )
    return {reaction["emoji"]: reaction["count"] for reaction in reactions_queryset}


def show_user_reactions(user: Model, instance: Model) -> list:
    """Show reactions' emojies of the current user with reactions' id"""

    user_reactions = list()
    if user.is_authenticated:
        user_reactions_query = instance.reactions.filter(
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
            author=user,
        ).only("emoji", "id")

        user_reactions = [
            {"type": reaction.emoji, "id": reaction.id}
            for reaction in user_reactions_query
        ]
    return user_reactions


def get_or_none(instance: Model, **kwargs):
    """Return an object if exists or None if does not exist"""

    try:
        return instance.objects.get(**kwargs)
    except instance.DoesNotExist:
        return None
