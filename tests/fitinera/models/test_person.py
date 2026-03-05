import pytest
from fitinera.models import Person, Age


def test_person_initialization_requires_id_and_ages():
    pass


def test_person_labels_dictionary_stores_string_facets():
    pass


def test_person_living_method_raises_not_implemented():
    person = Person("Alex", Age(30, 0), Age(100, 0))
    with pytest.raises(NotImplementedError):
        person.living()


def test_person_get_label_raises_not_implemented():
    person = Person("Alex", Age(30, 0), Age(100, 0))
    with pytest.raises(NotImplementedError):
        person.get_label("Status")
