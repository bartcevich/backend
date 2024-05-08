# Comment status
INVALID_ID_FORMAT: dict = {"detail": "Неверный формат id."}
COMMENT_NOT_FOUND: dict = {"detail": "Комментарий не найден."}
COMMENT_SUCCESSFULLY_DELETE: dict = {"message": "Комментарий удален!"}
CANT_EDIT_COMMENT: dict = (
    "Обновление комментария возможно только в течение суток после создания."
)

# User status
USER_DOES_NOT_EXISTS: dict = {"detail": "Пользователь не существует."}

# Author status
AUTHOR_IS_MISSING: dict = {"message": "Отсутствует автор."}
AUTHOR_NOT_FOUND: dict = {"message": "Автор не найден."}
SUCCESSFUL_ATTEMPT_ON_AUTHOR: dict = {"message": "Вы успешно подписались на автора."}
NOT_FOLLOWING_THIS_USER: dict = {"detail": "Вы не подписаны на этого пользователя."}
SUCCESSFUL_UNSUBSCRIBE_FROM_THE_AUTHOR: dict = {
    "message": "Вы успешно отписались от автора."
}

# Reaction status
REACTION_ALREADY_SET: dict = {"detail": "Вы уже поставили такую реакцию."}
SUCCESSFUL_RATED_IT: dict = {"message": "Вы поставили оценку!"}
SUCCESSFUL_LIKED_THE_RECIPE: dict = {"message": "Вы оценили рецепт!"}
REACTION_CANCELLED: dict = {"message": "Реакция отменена!"}
ALREADY_RATED_THIS_COMMENT: dict = {"detail": "Вы уже оценили данный комментарий."}
SUCCESSFUL_RATED_COMMENT: dict = {"message": "Вы оценили комментарий!"}

# Recipes status
RECIPE_SUCCESSFUL_DELETE: dict = {"message": "Рецепт успешно удален."}
RECIPE_ALREADY_IN_FAVORITES: dict = {"detail": "Рецепт уже находится в избранном."}
SUCCESSFUL_ADDED_TO_FAVORITES: dict = {"detail": "Рецепт добавлен в избранное."}
CREDENTIALS_WERE_NOT_PROVIDED: dict = {
    "detail": "Учетные данные не были предоставлены."
}
THE_RECIPE_IS_NOT_IN_FAVORITES: dict = {"detail": "Рецепт не находится в избранном."}
RECIPE_REMOVED_FROM_FAVORITES: dict = {"detail": "Рецепт удален из избранного."}
