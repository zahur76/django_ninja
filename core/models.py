from django.db import models


class Faction(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Character(models.Model):
    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"

    name = models.CharField(max_length=100)
    faction = models.ForeignKey(
        Faction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="characters",
    )
    # Star Wars dates use the BBY/ABY calendar (e.g. "19BBY"), so this is text, not a DateField.
    birth_date = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices)

    def __str__(self):
        return self.name
