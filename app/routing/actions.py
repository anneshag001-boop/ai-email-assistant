from app.routing.rules import FOLDER_MAP


class EmailActions:
    @staticmethod
    def get_folder_name(category_label: str) -> str:
        return FOLDER_MAP.get(category_label, "Others")

    @staticmethod
    def should_archive(category_label: str) -> bool:
        return category_label in ("others", "other_work")

    @staticmethod
    def should_auto_delete(category_label: str) -> bool:
        return category_label == "spam"

    @staticmethod
    def get_action(category: str) -> str:
        actions = {"spam": "delete_after_30_days", "others": "archive",
                   "other_work": "archive"}
        return actions.get(category, "move_to_folder")
