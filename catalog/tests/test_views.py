import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from catalog.models import Album, AlbumTrack, Artist, Song

from .factories import AlbumFactory, AlbumTrackFactory, ArtistFactory, SongFactory

pytestmark = pytest.mark.django_db


class TestPagesRender:
    def test_home(self, client):
        """Главная показывает сводку каталога."""
        AlbumFactory()
        response = client.get(reverse("catalog:home"))
        assert response.status_code == 200
        assert response.context["album_count"] == 1

    def test_artist_list_shows_album_count(self, client):
        """В списке исполнителей видно число альбомов."""
        artist = ArtistFactory(name="Queen")
        AlbumFactory(artist=artist)
        AlbumFactory(artist=artist)

        response = client.get(reverse("catalog:artist-list"))

        assert response.status_code == 200
        assert response.context["artists"][0].album_count == 2

    def test_artist_detail_lists_albums(self, client):
        """На карточке исполнителя перечислены его альбомы."""
        artist = ArtistFactory()
        album = AlbumFactory(artist=artist, title="Discovery")

        response = client.get(artist.get_absolute_url())

        assert response.status_code == 200
        assert album.title in response.content.decode()

    def test_album_detail_shows_tracklist_in_order(self, client):
        """Треклист отсортирован по номеру."""
        album = AlbumFactory()
        AlbumTrackFactory(album=album, song=SongFactory(title="Вторая"), track_number=2)
        AlbumTrackFactory(album=album, song=SongFactory(title="Первая"), track_number=1)

        response = client.get(album.get_absolute_url())
        body = response.content.decode()

        assert response.status_code == 200
        assert body.index("Первая") < body.index("Вторая")

    def test_song_detail_shows_every_album_with_its_number(self, client):
        """Карточка песни показывает разные номера."""
        song = SongFactory(title="Bohemian Rhapsody")
        opera = AlbumFactory(title="A Night at the Opera")
        hits = AlbumFactory(title="Greatest Hits")
        AlbumTrackFactory(album=opera, song=song, track_number=11)
        AlbumTrackFactory(album=hits, song=song, track_number=1)

        response = client.get(song.get_absolute_url())
        entries = {
            e.album.title: e.track_number
            for e in response.context["song"].album_entries.all()
        }

        assert response.status_code == 200
        assert entries == {"A Night at the Opera": 11, "Greatest Hits": 1}

    def test_song_list_shows_album_count(self, client):
        """В списке песен видно число альбомов."""
        song = SongFactory()
        AlbumTrackFactory(song=song, album=AlbumFactory(), track_number=1)
        AlbumTrackFactory(song=song, album=AlbumFactory(), track_number=1)

        response = client.get(reverse("catalog:song-list"))

        assert response.context["songs"][0].album_count == 2


class TestArtistCrud:
    def test_create(self, client):
        response = client.post(reverse("catalog:artist-create"), {"name": "Queen"})

        assert response.status_code == 302
        assert Artist.objects.filter(name="Queen").exists()

    def test_duplicate_name_rejected(self, client):
        """Дубликат отклоняется с сообщением, а не падением."""
        ArtistFactory(name="Queen")

        response = client.post(reverse("catalog:artist-create"), {"name": "Queen"})

        assert response.status_code == 200
        assert response.context["form"].errors
        assert Artist.objects.filter(name="Queen").count() == 1

    def test_update(self, client):
        artist = ArtistFactory(name="Quen")

        client.post(
            reverse("catalog:artist-update", args=[artist.pk]), {"name": "Queen"}
        )

        artist.refresh_from_db()
        assert artist.name == "Queen"

    def test_delete_removes_albums_but_keeps_songs(self, client):
        artist = ArtistFactory()
        album = AlbumFactory(artist=artist)
        AlbumTrackFactory(album=album, song=SongFactory(), track_number=1)

        response = client.post(reverse("catalog:artist-delete", args=[artist.pk]))

        assert response.status_code == 302
        assert Album.objects.count() == 0
        assert Song.objects.count() == 1


class TestAlbumCrud:
    def test_create(self, client):
        artist = ArtistFactory()

        response = client.post(
            reverse("catalog:album-create"),
            {"title": "Discovery", "artist": artist.pk, "release_year": 2001},
        )

        assert response.status_code == 302
        assert Album.objects.filter(title="Discovery", artist=artist).exists()

    def test_invalid_year_rejected(self, client):
        artist = ArtistFactory()

        response = client.post(
            reverse("catalog:album-create"),
            {"title": "Из будущего", "artist": artist.pk, "release_year": 2500},
        )

        assert response.status_code == 200
        assert "release_year" in response.context["form"].errors
        assert not Album.objects.exists()

    def test_duplicate_title_for_same_artist_rejected(self, client):
        """Дубликат заголовка для одного и того же исполнителя отклоняется."""
        artist = ArtistFactory()
        AlbumFactory(artist=artist, title="Greatest Hits")

        response = client.post(
            reverse("catalog:album-create"),
            {"title": "Greatest Hits", "artist": artist.pk, "release_year": 1990},
        )

        assert response.status_code == 200
        assert Album.objects.filter(title="Greatest Hits").count() == 1

    def test_delete(self, client):
        album = AlbumFactory()

        client.post(reverse("catalog:album-delete", args=[album.pk]))

        assert not Album.objects.exists()


class TestSongCrud:
    def test_create(self, client):
        response = client.post(reverse("catalog:song-create"), {"title": "Time"})

        assert response.status_code == 302
        assert Song.objects.filter(title="Time").exists()

    def test_delete_keeps_album(self, client):
        """Удаление песни убирает её из треклистов, но не затрагивает сами альбомы."""
        album = AlbumFactory()
        song = SongFactory()
        AlbumTrackFactory(album=album, song=song, track_number=1)

        client.post(reverse("catalog:song-delete", args=[song.pk]))

        assert Album.objects.filter(pk=album.pk).exists()
        assert AlbumTrack.objects.count() == 0


class TestTracklistManagement:
    def test_add_song_to_album(self, client):
        album, song = AlbumFactory(), SongFactory()

        response = client.post(
            reverse("catalog:track-create", args=[album.pk]),
            {"song": song.pk, "track_number": 4},
        )

        assert response.status_code == 302
        assert album.tracks.get(song=song).track_number == 4

    def test_same_song_added_to_second_album(self, client):
        """Ключевое требование через интерфейс: та же песня, другой номер."""
        song = SongFactory()
        first, second = AlbumFactory(), AlbumFactory()

        client.post(
            reverse("catalog:track-create", args=[first.pk]),
            {"song": song.pk, "track_number": 11},
        )
        client.post(
            reverse("catalog:track-create", args=[second.pk]),
            {"song": song.pk, "track_number": 1},
        )

        assert first.tracks.get(song=song).track_number == 11
        assert second.tracks.get(song=song).track_number == 1

    def test_taken_number_rejected_with_message(self, client):
        """Понятная ошибка, данные не изменились."""
        album = AlbumFactory()
        AlbumTrackFactory(album=album, track_number=3)

        response = client.post(
            reverse("catalog:track-create", args=[album.pk]),
            {"song": SongFactory().pk, "track_number": 3},
        )

        assert response.status_code == 200
        assert "track_number" in response.context["form"].errors
        assert album.tracks.count() == 1

    def test_duplicate_song_rejected_with_message(self, client):
        """Дубликат песни отклоняется с сообщением, а не падением."""
        album, song = AlbumFactory(), SongFactory()
        AlbumTrackFactory(album=album, song=song, track_number=1)

        response = client.post(
            reverse("catalog:track-create", args=[album.pk]),
            {"song": song.pk, "track_number": 2},
        )

        assert response.status_code == 200
        assert "song" in response.context["form"].errors
        assert album.tracks.count() == 1

    def test_change_track_number(self, client):
        track = AlbumTrackFactory(track_number=5)

        client.post(
            reverse("catalog:track-update", args=[track.pk]),
            {"song": track.song_id, "track_number": 2},
        )

        track.refresh_from_db()
        assert track.track_number == 2

    def test_editing_track_keeps_its_own_number_available(self, client):
        """Правка трека без смены номера не должна конфликтовать сама с собой."""
        track = AlbumTrackFactory(track_number=5)
        other_song = SongFactory()

        response = client.post(
            reverse("catalog:track-update", args=[track.pk]),
            {"song": other_song.pk, "track_number": 5},
        )

        assert response.status_code == 302
        track.refresh_from_db()
        assert track.song_id == other_song.pk

    def test_remove_track_from_album(self, client):
        """Удаление трека не трогает песню."""
        track = AlbumTrackFactory()

        client.post(reverse("catalog:track-delete", args=[track.pk]))

        assert AlbumTrack.objects.count() == 0
        assert Song.objects.count() == 1

    def test_add_form_suggests_next_number(self, client):
        album = AlbumFactory()
        AlbumTrackFactory(album=album, track_number=7)

        response = client.get(reverse("catalog:track-create", args=[album.pk]))

        assert response.context["form"].fields["track_number"].initial == 8


class TestSearchAndFilters:
    def test_artist_search(self, client):
        ArtistFactory(name="Queen")
        ArtistFactory(name="Pink Floyd")

        response = client.get(reverse("catalog:artist-list"), {"search": "que"})

        assert [a.name for a in response.context["artists"]] == ["Queen"]

    def test_album_search_by_title(self, client):
        AlbumFactory(title="Discovery")
        AlbumFactory(title="Homework")

        response = client.get(reverse("catalog:album-list"), {"search": "disc"})

        assert [a.title for a in response.context["albums"]] == ["Discovery"]

    def test_album_filter_by_artist(self, client):
        artist = ArtistFactory()
        AlbumFactory(artist=artist, title="Нужный")
        AlbumFactory(title="Лишний")

        response = client.get(reverse("catalog:album-list"), {"artist": artist.pk})

        assert [a.title for a in response.context["albums"]] == ["Нужный"]

    def test_album_filter_by_year(self, client):
        AlbumFactory(title="Старый", release_year=1975)
        AlbumFactory(title="Новый", release_year=2001)

        response = client.get(reverse("catalog:album-list"), {"year": 2001})

        assert [a.title for a in response.context["albums"]] == ["Новый"]

    def test_song_search(self, client):
        SongFactory(title="Bohemian Rhapsody")
        SongFactory(title="Money")

        response = client.get(reverse("catalog:song-list"), {"search": "rhaps"})

        assert [s.title for s in response.context["songs"]] == ["Bohemian Rhapsody"]

    def test_pagination_keeps_active_filters(self, client):
        """Переход на следующую страницу не должен сбрасывать фильтр."""
        artist = ArtistFactory()
        for number in range(30):
            AlbumFactory(artist=artist, title=f"Альбом {number:02d}")
        AlbumFactory(title="Чужой альбом")

        first_page = client.get(reverse("catalog:album-list"), {"artist": artist.pk})
        body = first_page.content.decode()

        assert first_page.context["is_paginated"]
        assert f"artist={artist.pk}" in body, (
            "ссылка на следующую страницу потеряла фильтр"
        )

        second_page = client.get(
            reverse("catalog:album-list"), {"artist": artist.pk, "page": 2}
        )

        assert all(
            album.artist_id == artist.pk for album in second_page.context["albums"]
        )


class TestQueryCounts:
    """Число запросов не растёт вместе с числом строк на странице."""

    @staticmethod
    def _queries_for(client, url) -> int:
        with CaptureQueriesContext(connection) as ctx:
            client.get(url)
        return len(ctx.captured_queries)

    def test_album_list_has_no_n_plus_one(self, client):
        for _ in range(3):
            AlbumFactory()
        baseline = self._queries_for(client, reverse("catalog:album-list"))

        for _ in range(10):
            AlbumFactory()

        assert self._queries_for(client, reverse("catalog:album-list")) == baseline

    def test_album_detail_has_no_n_plus_one(self, client):
        album = AlbumFactory()
        for number in range(1, 4):
            AlbumTrackFactory(album=album, track_number=number)
        baseline = self._queries_for(client, album.get_absolute_url())

        for number in range(4, 15):
            AlbumTrackFactory(album=album, track_number=number)

        assert self._queries_for(client, album.get_absolute_url()) == baseline

    def test_song_detail_has_no_n_plus_one(self, client):
        song = SongFactory()
        for _ in range(3):
            AlbumTrackFactory(album=AlbumFactory(), song=song, track_number=1)
        baseline = self._queries_for(client, song.get_absolute_url())

        for _ in range(10):
            AlbumTrackFactory(album=AlbumFactory(), song=song, track_number=1)

        assert self._queries_for(client, song.get_absolute_url()) == baseline
