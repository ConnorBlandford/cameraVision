from camera_vision.detection.classes import resolve_target_class


def test_known_aliases():
    assert resolve_target_class("Apples") == "apple"
    assert resolve_target_class("apple") == "apple"
    assert resolve_target_class("oranges") == "orange"


def test_unknown_target_returns_none():
    assert resolve_target_class("corks") is None
    assert resolve_target_class("rubber duck") is None
    assert resolve_target_class("") is None


def test_generic_plural_stripping():
    # "cats" -> "cat"
    assert resolve_target_class("Cats") == "cat"
