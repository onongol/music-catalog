import pytest
from django.core.management import call_command

from catalog.models import Album, AlbumTrack, Artist, Song

pytestmark = pytest.mark.django_db


@pytest.fixture
def seeded():
    call_command("seed_demo", verbosity=0)


def test_creates_catalog(seeded):
    assert Artist.objects.exists()
    assert Album.objects.exists()
    assert Song.objects.exists()
    assert AlbumTrack.objects.exists()


def test_contains_song_in_two_albums_with_different_numbers(seeded):
    """Демо-набор обязан показывать ключевой случай сразу после установки."""
    song = Song.objects.get(title="Bohemian Rhapsody")
    numbers = {
        e.album.title: e.track_number
        for e in song.album_entries.select_related("album")
    }

    assert len(numbers) == 2
    assert len(set(numbers.values())) == 2


def test_is_idempotent(seeded):
    """Повторный запуск не создаёт дублей."""
    before = (
        Artist.objects.count(),
        Album.objects.count(),
        Song.objects.count(),
        AlbumTrack.objects.count(),
    )

    call_command("seed_demo", verbosity=0)

    after = (
        Artist.objects.count(),
        Album.objects.count(),
        Song.objects.count(),
        AlbumTrack.objects.count(),
    )
    assert before == after


def test_reset_clears_and_reloads(seeded):
    counts = Album.objects.count()

    call_command("seed_demo", "--reset", verbosity=0)

    assert Album.objects.count() == counts


def test_no_duplicate_numbers_within_album(seeded):
    """Демо-данные не нарушают инвариант."""
    for album in Album.objects.prefetch_related("tracks"):
        numbers = [t.track_number for t in album.tracks.all()]
        assert len(numbers) == len(set(numbers))
