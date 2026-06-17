import pytest
from app.routing.router import route_email
from app.routing.actions import EmailActions


def test_route_spam():
    r = route_email("spam", "business", 0.9, 0.0)
    assert r["routed_folder"] == "Spam"
    assert r["routed_action"] == "delete_after_30_days"


def test_route_category_spam():
    r = route_email("not_spam", "spam", 0.9, 0.0)
    assert r["routed_folder"] == "Spam"
    assert r["routed_action"] == "delete_after_30_days"


def test_route_business():
    r = route_email("not_spam", "business", 0.8, 0.0)
    assert r["routed_folder"] == "Business"
    assert r["routed_action"] == "move_to_folder"


def test_route_private():
    r = route_email("not_spam", "private", 0.9, 0.0)
    assert r["routed_folder"] == "Private"
    assert r["routed_action"] == "move_to_folder"


def test_route_other_work():
    r = route_email("not_spam", "other_work", 0.8, 0.0)
    assert r["routed_folder"] == "Other Work"
    assert r["routed_action"] == "archive"


def test_route_others():
    r = route_email("not_spam", "others", 0.8, 0.0)
    assert r["routed_folder"] == "Others"
    assert r["routed_action"] == "archive"


def test_folder_name():
    assert EmailActions.get_folder_name("spam") == "Spam"
    assert EmailActions.get_folder_name("business") == "Business"
    assert EmailActions.get_folder_name("private") == "Private"
    assert EmailActions.get_folder_name("other_work") == "Other Work"
    assert EmailActions.get_folder_name("others") == "Others"


def test_auto_delete():
    assert EmailActions.should_auto_delete("spam") is True
    assert EmailActions.should_auto_delete("business") is False
