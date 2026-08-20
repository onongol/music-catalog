"""Наполнение каталога демонстрационными данными.

Повторный запуск не создаёт дублей и не меняет уже
существующие записи. Набор данных подобран так, чтобы сразу был виден ключевой
случай — одна песня в двух альбомах под разными номерами.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Album, AlbumTrack, Artist, Song

# (исполнитель, альбом, год, [(номер, песня), ...])
DEMO_DATA = [
    (
        "Queen",
        "A Night at the Opera",
        1975,
        [
            (1, "Death on Two Legs"),
            (2, "Lazing on a Sunday Afternoon"),
            (4, "You're My Best Friend"),
            (11, "Bohemian Rhapsody"),
            (12, "God Save the Queen"),
        ],
    ),
    (
        "Queen",
        "Greatest Hits",
        1981,
        [
            # Те же песни, что и выше, но под другими номерами — суть требования.
            (1, "Bohemian Rhapsody"),
            (2, "Another One Bites the Dust"),
            (5, "You're My Best Friend"),
            (9, "We Will Rock You"),
        ],
    ),
    (
        "Pink Floyd",
        "The Dark Side of the Moon",
        1973,
        [
            (1, "Speak to Me"),
            (2, "Breathe (In the Air)"),
            (4, "Time"),
            (6, "Money"),
        ],
    ),
    (
        "Pink Floyd",
        "Echoes: The Best of Pink Floyd",
        2001,
        [
            (3, "Money"),
            (7, "Time"),
            (11, "Wish You Were Here"),
        ],
    ),
    (
        "Daft Punk",
        "Discovery",
        2001,
        [
            (1, "One More Time"),
            (2, "Aerodynamic"),
            (3, "Digital Love"),
            (4, "Harder, Better, Faster, Stronger"),
        ],
    ),
]


class Command(BaseCommand):
    help = "Load demo catalog data (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Wipe the catalog before loading.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            AlbumTrack.objects.all().delete()
            Album.objects.all().delete()
            Song.objects.all().delete()
            Artist.objects.all().delete()
            self.stdout.write("Catalog cleared.")

        created = {"artists": 0, "albums": 0, "songs": 0, "tracks": 0}

        for artist_name, album_title, year, tracklist in DEMO_DATA:
            artist, is_new = Artist.objects.get_or_create(name=artist_name)
            created["artists"] += is_new

            album, is_new = Album.objects.get_or_create(
                artist=artist,
                title=album_title,
                defaults={"release_year": year},
            )
            created["albums"] += is_new

            for number, song_title in tracklist:
                # Песня ищется по названию: она общая для всех альбомов,
                # где встречается, — именно это и демонстрирует набор данных.
                song, is_new = Song.objects.get_or_create(title=song_title)
                created["songs"] += is_new

                _, is_new = AlbumTrack.objects.get_or_create(
                    album=album,
                    song=song,
                    defaults={"track_number": number},
                )
                created["tracks"] += is_new

        self.stdout.write(
            self.style.SUCCESS(
                "Demo data loaded. Created: "
                f"{created['artists']} artists, "
                f"{created['albums']} albums, "
                f"{created['songs']} songs, "
                f"{created['tracks']} tracks."
            )
        )

        shared = (
            Song.objects.filter(title="Bohemian Rhapsody")
            .prefetch_related("album_entries__album")
            .first()
        )
        if shared:
            places = ", ".join(
                f'"{entry.album.title}" #{entry.track_number}'
                for entry in shared.album_entries.all()
            )
            self.stdout.write(f'Shared song example: "{shared.title}" -> {places}')
