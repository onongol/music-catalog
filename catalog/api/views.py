from django.db.models import Count, Prefetch
from rest_framework import viewsets

from catalog.api.serializers import (
    AlbumSerializer,
    AlbumTrackSerializer,
    ArtistSerializer,
    SongSerializer,
)
from catalog.models import Album, AlbumTrack, Artist, Song


class ArtistViewSet(viewsets.ModelViewSet):
    """Исполнители: CRUD, поиск по имени."""

    serializer_class = ArtistSerializer
    search_fields = ["name"]
    ordering_fields = ["name"]
    queryset = (
        Artist.objects.annotate(album_count=Count("albums", distinct=True))
        .prefetch_related("albums")
        .order_by("name")
    )


class AlbumViewSet(viewsets.ModelViewSet):
    """Альбомы: CRUD, фильтр по исполнителю и году, вложенный треклист."""

    serializer_class = AlbumSerializer
    filterset_fields = ["artist", "release_year"]
    search_fields = ["title", "artist__name"]
    ordering_fields = ["title", "release_year", "artist__name"]
    queryset = (
        Album.objects.select_related("artist")
        .annotate(track_count=Count("tracks", distinct=True))
        .prefetch_related(
            Prefetch(
                "tracks",
                queryset=AlbumTrack.objects.select_related("song").order_by(
                    "track_number"
                ),
            )
        )
        .order_by("artist__name", "release_year")
    )


class SongViewSet(viewsets.ModelViewSet):
    """Песни: CRUD, поиск по названию, список альбомов с номерами."""

    serializer_class = SongSerializer
    search_fields = ["title"]
    ordering_fields = ["title"]
    queryset = (
        Song.objects.annotate(album_count=Count("album_entries", distinct=True))
        .prefetch_related(
            Prefetch(
                "album_entries",
                queryset=AlbumTrack.objects.select_related("album__artist").order_by(
                    "album__release_year"
                ),
            )
        )
        .order_by("title")
    )


class AlbumTrackViewSet(viewsets.ModelViewSet):
    """Треки: добавление песни в альбом, смена номера, удаление из альбома."""

    serializer_class = AlbumTrackSerializer
    filterset_fields = ["album", "song", "track_number"]
    search_fields = ["song__title", "album__title"]
    ordering_fields = ["track_number"]
    queryset = AlbumTrack.objects.select_related("album__artist", "song").order_by(
        "album__title", "track_number"
    )
