from django.core.management.base import BaseCommand

from core.models import Character, Faction

FACTIONS = [
    "Rebel Alliance",
    "Galactic Empire",
    "Jedi Order",
    "Sith",
    "Galactic Republic",
]

# (name, faction name or None, birth_date, gender)
CHARACTERS = [
    # Rebel Alliance
    ("Luke Skywalker", "Rebel Alliance", "19BBY", "male"),
    ("Leia Organa", "Rebel Alliance", "19BBY", "female"),
    ("Han Solo", "Rebel Alliance", "32BBY", "male"),
    ("Chewbacca", "Rebel Alliance", "200BBY", "male"),
    ("Lando Calrissian", "Rebel Alliance", "31BBY", "male"),
    ("Mon Mothma", "Rebel Alliance", "48BBY", "female"),
    ("Wedge Antilles", "Rebel Alliance", "21BBY", "male"),
    ("R2-D2", "Rebel Alliance", "33BBY", "other"),
    ("C-3PO", "Rebel Alliance", "112BBY", "other"),
    # Galactic Empire
    ("Darth Vader", "Galactic Empire", "41BBY", "male"),
    ("Grand Moff Tarkin", "Galactic Empire", "64BBY", "male"),
    # Jedi Order
    ("Obi-Wan Kenobi", "Jedi Order", "57BBY", "male"),
    ("Yoda", "Jedi Order", "896BBY", "male"),
    ("Mace Windu", "Jedi Order", "72BBY", "male"),
    ("Qui-Gon Jinn", "Jedi Order", "92BBY", "male"),
    ("Ahsoka Tano", "Jedi Order", "36BBY", "female"),
    # Sith
    ("Darth Sidious", "Sith", "84BBY", "male"),
    ("Darth Maul", "Sith", "54BBY", "male"),
    ("Count Dooku", "Sith", "102BBY", "male"),
    # Galactic Republic
    ("Padmé Amidala", "Galactic Republic", "46BBY", "female"),
    # No faction
    ("Boba Fett", None, "32BBY", "male"),
    ("Jabba the Hutt", None, "600BBY", "male"),
]


class Command(BaseCommand):
    help = "Load sample Star Wars factions and characters into the database."

    def handle(self, *args, **options):
        factions = {}
        for name in FACTIONS:
            factions[name], created = Faction.objects.get_or_create(name=name)
            self.stdout.write(f"{'Created' if created else 'Exists '}  faction    {name}")

        for name, faction_name, birth_date, gender in CHARACTERS:
            _, created = Character.objects.update_or_create(
                name=name,
                defaults={
                    "faction": factions[faction_name] if faction_name else None,
                    "birth_date": birth_date,
                    "gender": gender,
                },
            )
            self.stdout.write(f"{'Created' if created else 'Updated'}  character  {name}")

        self.stdout.write(self.style.SUCCESS(
            f"Done: {Faction.objects.count()} factions, {Character.objects.count()} characters in database."
        ))
