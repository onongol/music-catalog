from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from catalog.models import Album, AlbumTrack, Artist, Song

from .factories import AlbumFactory, AlbumTrackFactory, ArtistFactory, SongFactory

pytestmark = pytest.mark.django_db


class TestArtist:
    def test_name_is_unique(self):
        """Имя исполнителя уникально."""
        ArtistFactory(name="Queen")
        with pytest.raises(IntegrityError):
            Artist.objects.create(name="Queen")

    def test_str(self):
        assert str(ArtistFactory(name="Queen")) == "Queen"


class TestAlbum:
    def test_title_unique_per_artist(self):
        """Пара «исполнитель + название» уникальна."""
        artist = ArtistFactory()
        AlbumFactory(artist=artist, title="Greatest Hits")
        with pytest.raises(IntegrityError):
            Album.objects.create(
                artist=artist, title="Greatest Hits", release_year=1990
            )

    def test_same_title_allowed_for_other_artist(self):
        """Разные исполнители могут иметь одноимённые альбомы."""
        AlbumFactory(artist=ArtistFactory(name="A"), title="Greatest Hits")
        AlbumFactory(artist=ArtistFactory(name="B"), title="Greatest Hits")
        assert Album.objects.filter(title="Greatest Hits").count() == 2

    @pytest.mark.parametrize("year", [1859, 0])
    def test_year_below_range_rejected(self, year):
        """Слишком ранний год не проходит валидацию."""
        album = AlbumFactory.build(artist=ArtistFactory(), release_year=year)
        with pytest.raises(ValidationError):
            album.full_clean()

    def test_year_in_future_rejected(self):
        """Год позже «следующего» не проходит валидацию."""
        album = AlbumFactory.build(
            artist=ArtistFactory(), release_year=date.today().year + 5
        )
        with pytest.raises(ValidationError):
            album.full_clean()

    def test_next_year_allowed(self):
        """Анонсированный альбом следующего года допустим."""
        album = AlbumFactory.build(
            artist=ArtistFactory(), release_year=date.today().year + 1
        )
        album.full_clean()

    def test_next_track_number(self):
        album = AlbumFactory()
        assert album.next_track_number() == 1
        AlbumTrackFactory(album=album, track_number=7)
        assert album.next_track_number() == 8


class TestAlbumTrack:
    def test_track_number_unique_within_album(self):
        """Два трека альбома не могут иметь одинаковый номер."""
        album = AlbumFactory()
        AlbumTrackFactory(album=album, track_number=3)
        with pytest.raises(IntegrityError):
            AlbumTrack.objects.create(album=album, song=SongFactory(), track_number=3)

    def test_song_added_to_album_only_once(self):
        """Одна песня не может входить в альбом дважды."""
        album, song = AlbumFactory(), SongFactory()
        AlbumTrackFactory(album=album, song=song, track_number=1)
        with pytest.raises(IntegrityError):
            AlbumTrack.objects.create(album=album, song=song, track_number=2)

    def test_zero_track_number_rejected(self):
        """Номер трека — целое число ≥ 1."""
        track = AlbumTrackFactory.build(
            album=AlbumFactory(), song=SongFactory(), track_number=0
        )
        with pytest.raises(ValidationError):
            track.full_clean()


class TestKeyRequirement:
    """Одна песня в двух альбомах с разными номерами."""

    def test_song_in_two_albums_with_different_numbers(self):
        queen = ArtistFactory(name="Queen")
        opera = AlbumFactory(
            artist=queen, title="A Night at the Opera", release_year=1975
        )
        hits = AlbumFactory(artist=queen, title="Greatest Hits", release_year=1981)
        rhapsody = SongFactory(title="Bohemian Rhapsody")

        AlbumTrackFactory(album=opera, song=rhapsody, track_number=11)
        AlbumTrackFactory(album=hits, song=rhapsody, track_number=1)

        # Песня хранится в единственном экземпляре.
        assert Song.objects.filter(title="Bohemian Rhapsody").count() == 1

        # Номера в альбомах различаются.
        assert opera.tracks.get(song=rhapsody).track_number == 11
        assert hits.tracks.get(song=rhapsody).track_number == 1

        # С точки зрения песни видны оба вхождения.
        numbers = {e.album.title: e.track_number for e in rhapsody.album_entries.all()}
        assert numbers == {"A Night at the Opera": 11, "Greatest Hits": 1}

    def test_same_number_in_different_albums_is_allowed(self):
        """Номер 1 может существовать в каждом альбоме — ограничение только внутри альбома."""
        song = SongFactory()
        AlbumTrackFactory(album=AlbumFactory(), song=song, track_number=1)
        AlbumTrackFactory(album=AlbumFactory(), song=song, track_number=1)
        assert AlbumTrack.objects.filter(song=song, track_number=1).count() == 2


class TestCascades:
    def test_deleting_artist_keeps_songs(self):
        """Удаляются альбомы, песни остаются."""
        artist = ArtistFactory()
        album = AlbumFactory(artist=artist)
        AlbumTrackFactory(album=album, song=SongFactory(), track_number=1)
        AlbumTrackFactory(album=album, song=SongFactory(), track_number=2)

        artist.delete()

        assert Album.objects.count() == 0
        assert AlbumTrack.objects.count() == 0
        assert Song.objects.count() == 2

    def test_deleting_song_keeps_albums(self):
        """Песня уходит из треклистов, альбомы остаются."""
        album = AlbumFactory()
        song = SongFactory()
        AlbumTrackFactory(album=album, song=song, track_number=1)

        song.delete()

        assert Album.objects.filter(pk=album.pk).exists()
        assert album.tracks.count() == 0

    def test_deleting_album_keeps_songs(self):
        album = AlbumFactory()
        song = SongFactory()
        AlbumTrackFactory(album=album, song=song, track_number=1)

        album.delete()

        assert Song.objects.filter(pk=song.pk).exists()
        assert AlbumTrack.objects.count() == 0

    def test_removing_track_touches_nothing_else(self):
        album, song = AlbumFactory(), SongFactory()
        track = AlbumTrackFactory(album=album, song=song, track_number=1)

        track.delete()

        assert Album.objects.filter(pk=album.pk).exists()
        assert Song.objects.filter(pk=song.pk).exists()


class TestOrdering:
    def test_tracks_ordered_by_number(self):
        """Треклист отсортирован по порядковому номеру."""
        album = AlbumFactory()
        for number in (5, 1, 3):
            AlbumTrackFactory(album=album, track_number=number)

        assert list(album.tracks.values_list("track_number", flat=True)) == [1, 3, 5]

    def test_albums_of_artist_ordered_by_year(self):
        """Альбомы исполнителя отсортированы по году."""
        artist = ArtistFactory()
        for year in (1990, 1975, 1983):
            AlbumFactory(artist=artist, release_year=year)

        years = list(
            artist.albums.order_by("release_year").values_list(
                "release_year", flat=True
            )
        )
        assert years == [1975, 1983, 1990]


def test_constraint_rollback_leaves_data_intact():
    """Отклонённая операция не изменяет данные."""
    album = AlbumFactory()
    AlbumTrackFactory(album=album, track_number=3)

    with pytest.raises(IntegrityError), transaction.atomic():
        AlbumTrack.objects.create(album=album, song=SongFactory(), track_number=3)

    assert album.tracks.count() == 1
