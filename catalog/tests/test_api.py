import pytest
from rest_framework.test import APIClient

from catalog.models import Album, AlbumTrack, Artist, Song

from .factories import AlbumFactory, AlbumTrackFactory, ArtistFactory, SongFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def api():
    return APIClient()


class TestArtistApi:
    def test_list(self, api):
        ArtistFactory(name="Queen")
        response = api.get("/api/artists/")

        assert response.status_code == 200
        assert response.data["results"][0]["name"] == "Queen"

    def test_list_includes_album_count(self, api):
        artist = ArtistFactory()
        AlbumFactory(artist=artist)
        AlbumFactory(artist=artist)

        response = api.get("/api/artists/")

        assert response.data["results"][0]["album_count"] == 2

    def test_create(self, api):
        response = api.post("/api/artists/", {"name": "Daft Punk"}, format="json")

        assert response.status_code == 201
        assert response.data["album_count"] == 0
        assert Artist.objects.filter(name="Daft Punk").exists()

    def test_duplicate_name_returns_400(self, api):
        ArtistFactory(name="Queen")
        response = api.post("/api/artists/", {"name": "Queen"}, format="json")

        assert response.status_code == 400

    def test_search(self, api):
        ArtistFactory(name="Queen")
        ArtistFactory(name="Pink Floyd")

        response = api.get("/api/artists/", {"search": "que"})

        assert response.data["count"] == 1

    def test_delete(self, api):
        artist = ArtistFactory()
        response = api.delete(f"/api/artists/{artist.pk}/")

        assert response.status_code == 204
        assert not Artist.objects.exists()


class TestAlbumApi:
    def test_detail_contains_nested_tracklist(self, api):
        album = AlbumFactory()
        AlbumTrackFactory(album=album, song=SongFactory(title="Time"), track_number=4)

        response = api.get(f"/api/albums/{album.pk}/")

        assert response.status_code == 200
        assert response.data["track_count"] == 1
        assert response.data["tracks"][0]["track_number"] == 4
        assert response.data["tracks"][0]["song_title"] == "Time"

    def test_tracklist_is_ordered(self, api):
        album = AlbumFactory()
        for number in (9, 2, 5):
            AlbumTrackFactory(album=album, track_number=number)

        response = api.get(f"/api/albums/{album.pk}/")

        assert [t["track_number"] for t in response.data["tracks"]] == [2, 5, 9]

    def test_create(self, api):
        artist = ArtistFactory()
        response = api.post(
            "/api/albums/",
            {"title": "Discovery", "artist": artist.pk, "release_year": 2001},
            format="json",
        )

        assert response.status_code == 201
        assert response.data["artist_name"] == artist.name
        assert Album.objects.filter(title="Discovery").exists()

    def test_invalid_year_returns_400(self, api):
        response = api.post(
            "/api/albums/",
            {
                "title": "Из будущего",
                "artist": ArtistFactory().pk,
                "release_year": 3000,
            },
            format="json",
        )

        assert response.status_code == 400
        assert "release_year" in response.data

    def test_duplicate_album_returns_400(self, api):
        """Пара «исполнитель + название альбома» уникальна."""
        artist = ArtistFactory()
        AlbumFactory(artist=artist, title="Greatest Hits")

        response = api.post(
            "/api/albums/",
            {"title": "Greatest Hits", "artist": artist.pk, "release_year": 1990},
            format="json",
        )

        assert response.status_code == 400

    def test_filter_by_artist_and_year(self, api):
        artist = ArtistFactory()
        AlbumFactory(artist=artist, title="Нужный", release_year=1975)
        AlbumFactory(artist=artist, title="Другой год", release_year=1999)
        AlbumFactory(title="Другой артист", release_year=1975)

        response = api.get("/api/albums/", {"artist": artist.pk, "release_year": 1975})

        assert response.data["count"] == 1
        assert response.data["results"][0]["title"] == "Нужный"

    def test_partial_update(self, api):
        album = AlbumFactory(release_year=1975)

        response = api.patch(
            f"/api/albums/{album.pk}/", {"release_year": 1976}, format="json"
        )

        assert response.status_code == 200
        album.refresh_from_db()
        assert album.release_year == 1976


class TestSongApi:
    def test_detail_lists_every_appearance(self, api):
        song = SongFactory(title="Bohemian Rhapsody")
        opera = AlbumFactory(title="A Night at the Opera", release_year=1975)
        hits = AlbumFactory(title="Greatest Hits", release_year=1981)
        AlbumTrackFactory(album=opera, song=song, track_number=11)
        AlbumTrackFactory(album=hits, song=song, track_number=1)

        response = api.get(f"/api/songs/{song.pk}/")

        assert response.status_code == 200
        assert response.data["album_count"] == 2
        numbers = {
            a["album_title"]: a["track_number"] for a in response.data["appears_on"]
        }
        assert numbers == {"A Night at the Opera": 11, "Greatest Hits": 1}

    def test_create(self, api):
        response = api.post("/api/songs/", {"title": "Money"}, format="json")

        assert response.status_code == 201
        assert response.data["album_count"] == 0
        assert Song.objects.filter(title="Money").exists()

    def test_search(self, api):
        SongFactory(title="Bohemian Rhapsody")
        SongFactory(title="Money")

        response = api.get("/api/songs/", {"search": "rhaps"})

        assert response.data["count"] == 1

    def test_delete_keeps_albums(self, api):
        album = AlbumFactory()
        song = SongFactory()
        AlbumTrackFactory(album=album, song=song, track_number=1)

        response = api.delete(f"/api/songs/{song.pk}/")

        assert response.status_code == 204
        assert Album.objects.filter(pk=album.pk).exists()
        assert AlbumTrack.objects.count() == 0


class TestTrackApi:
    def test_add_song_to_album(self, api):
        album, song = AlbumFactory(), SongFactory()

        response = api.post(
            "/api/tracks/",
            {"album": album.pk, "song": song.pk, "track_number": 4},
            format="json",
        )

        assert response.status_code == 201
        assert album.tracks.get(song=song).track_number == 4

    def test_same_song_two_albums_different_numbers(self, api):
        """Ключевое требование через API."""
        song = SongFactory()
        first, second = AlbumFactory(), AlbumFactory()

        api.post(
            "/api/tracks/",
            {"album": first.pk, "song": song.pk, "track_number": 11},
            format="json",
        )
        api.post(
            "/api/tracks/",
            {"album": second.pk, "song": song.pk, "track_number": 1},
            format="json",
        )

        assert first.tracks.get(song=song).track_number == 11
        assert second.tracks.get(song=song).track_number == 1

    def test_taken_number_returns_400(self, api):
        album = AlbumFactory()
        AlbumTrackFactory(album=album, track_number=3)

        response = api.post(
            "/api/tracks/",
            {"album": album.pk, "song": SongFactory().pk, "track_number": 3},
            format="json",
        )

        assert response.status_code == 400
        assert "3" in str(response.data)
        assert album.tracks.count() == 1

    def test_duplicate_song_returns_400(self, api):
        album, song = AlbumFactory(), SongFactory()
        AlbumTrackFactory(album=album, song=song, track_number=1)

        response = api.post(
            "/api/tracks/",
            {"album": album.pk, "song": song.pk, "track_number": 2},
            format="json",
        )

        assert response.status_code == 400
        assert album.tracks.count() == 1

    def test_change_number(self, api):
        track = AlbumTrackFactory(track_number=5)

        response = api.patch(
            f"/api/tracks/{track.pk}/", {"track_number": 2}, format="json"
        )

        assert response.status_code == 200
        track.refresh_from_db()
        assert track.track_number == 2

    def test_patch_keeping_own_number_is_allowed(self, api):
        """Частичное обновление не должно конфликтовать с самим собой."""
        track = AlbumTrackFactory(track_number=5)

        response = api.patch(
            f"/api/tracks/{track.pk}/", {"track_number": 5}, format="json"
        )

        assert response.status_code == 200

    def test_filter_by_album(self, api):
        album = AlbumFactory()
        AlbumTrackFactory(album=album, track_number=1)
        AlbumTrackFactory(album=AlbumFactory(), track_number=1)

        response = api.get("/api/tracks/", {"album": album.pk})

        assert response.data["count"] == 1

    def test_delete_removes_only_the_entry(self, api):
        track = AlbumTrackFactory()

        response = api.delete(f"/api/tracks/{track.pk}/")

        assert response.status_code == 204
        assert AlbumTrack.objects.count() == 0
        assert Song.objects.count() == 1
        assert Album.objects.count() == 1


def test_api_root_is_browsable(api):
    """Корень API перечисляет ресурсы."""
    response = api.get("/api/")

    assert response.status_code == 200
    assert set(response.data) == {"artists", "albums", "songs", "tracks"}
