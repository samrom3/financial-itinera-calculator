from fitinera.models import Person, Age


class TestPersonInitialization:
    """Tests for Person dataclass construction."""

    def test_person_initialization_requires_id_and_ages(self):
        """Person can be constructed with id, age, and expectancy.

        Verifies the basic dataclass fields are stored correctly.
        """
        person = Person(id="Alex", age=Age(30, 0), expectancy=Age(100, 0))
        assert person.id == "Alex"
        assert person.age == Age(30, 0)
        assert person.expectancy == Age(100, 0)

    def test_person_labels_dictionary_stores_string_facets(self):
        """Person labels dict stores string facet-value pairs.

        Labels are optional; when provided they must be readable by key.
        """
        person = Person(
            id="Alex",
            age=Age(30, 0),
            expectancy=Age(100, 0),
            labels={"Status": "active"},
        )
        assert person.labels["Status"] == "active"


class TestPersonLiving:
    """Tests for Person.living() method."""

    def test_living_returns_true_when_age_is_clearly_younger_than_expectancy(self):
        """Person.living returns True when current years < expectancy years.

        A person aged 30 with expectancy 100 is clearly living.
        """
        person = Person(id="Alex", age=Age(30, 0), expectancy=Age(100, 0))
        assert person.living() is True

    def test_living_returns_false_when_age_exceeds_expectancy_years(self):
        """Person.living returns False when current years > expectancy years.

        A person aged 101 with expectancy 100 has exceeded their expectancy.
        """
        person = Person(id="Alex", age=Age(101, 0), expectancy=Age(100, 0))
        assert person.living() is False

    def test_living_returns_false_when_age_years_equal_and_months_equal(self):
        """Person.living returns False when age years and months equal expectancy.

        At exactly the expectancy boundary (years equal, months equal) the person
        is not living (living requires strictly less than).
        """
        person = Person(id="Alex", age=Age(100, 0), expectancy=Age(100, 0))
        assert person.living() is False

    def test_living_returns_true_when_years_equal_but_months_strictly_less(self):
        """Person.living returns True when years equal but months < expectancy months.

        Age 99y 11m vs expectancy 100y 0m: years equal is False (99 < 100), so True.
        """
        person = Person(id="Alex", age=Age(99, 11), expectancy=Age(100, 0))
        assert person.living() is True

    def test_living_returns_false_when_years_equal_and_months_exceed_expectancy(self):
        """Person.living returns False when years equal and months >= expectancy months.

        Age 100y 6m vs expectancy 100y 0m: years equal (100 == 100) and
        months (6) >= expectancy months (0), so not living.
        """
        person = Person(id="Alex", age=Age(100, 6), expectancy=Age(100, 0))
        assert person.living() is False

    def test_living_returns_true_when_same_years_and_months_strictly_less(self):
        """Person.living returns True when years equal and months strictly less.

        Age 100y 5m vs expectancy 100y 6m: years equal (100 == 100) and
        months (5) < expectancy months (6), so living.
        """
        person = Person(id="Alex", age=Age(100, 5), expectancy=Age(100, 6))
        assert person.living() is True


class TestPersonGetLabel:
    """Tests for Person.get_label() method."""

    def test_get_label_returns_value_for_existing_facet(self):
        """Person.get_label returns the label value string for a known facet."""
        person = Person(
            id="Alex",
            age=Age(30, 0),
            expectancy=Age(100, 0),
            labels={"Status": "active"},
        )
        assert person.get_label("Status") == "active"

    def test_get_label_returns_none_for_missing_facet(self):
        """Person.get_label returns None when the facet is not present."""
        person = Person(
            id="Alex",
            age=Age(30, 0),
            expectancy=Age(100, 0),
            labels={"Status": "active"},
        )
        assert person.get_label("Role") is None

    def test_get_label_returns_none_when_labels_empty(self):
        """Person.get_label returns None when labels dict is empty."""
        person = Person(id="Alex", age=Age(30, 0), expectancy=Age(100, 0))
        assert person.get_label("Status") is None
