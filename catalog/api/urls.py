from django.urls import include, path
from rest_framework.routers import DefaultRouter

from catalog.api.views import (
    AlbumTrackViewSet,
    AlbumViewSet,
    ArtistViewSet,
    SongViewSet,
)

app_name = "api"

router = DefaultRouter()
router.register("artists", ArtistViewSet, basename="artist")
router.register("albums", AlbumViewSet, basename="album")
router.register("songs", SongViewSet, basename="song")
router.register("tracks", AlbumTrackViewSet, basename="track")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("rest_framework.urls", namespace="rest_framework")),
]
