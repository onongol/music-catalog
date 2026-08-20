from django.urls import path

from catalog import views

app_name = "catalog"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    # Исполнители
    path("artists/", views.ArtistListView.as_view(), name="artist-list"),
    path("artists/add/", views.ArtistCreateView.as_view(), name="artist-create"),
    path("artists/<int:pk>/", views.ArtistDetailView.as_view(), name="artist-detail"),
    path(
        "artists/<int:pk>/edit/", views.ArtistUpdateView.as_view(), name="artist-update"
    ),
    path(
        "artists/<int:pk>/delete/",
        views.ArtistDeleteView.as_view(),
        name="artist-delete",
    ),
    # Альбомы
    path("albums/", views.AlbumListView.as_view(), name="album-list"),
    path("albums/add/", views.AlbumCreateView.as_view(), name="album-create"),
    path("albums/<int:pk>/", views.AlbumDetailView.as_view(), name="album-detail"),
    path("albums/<int:pk>/edit/", views.AlbumUpdateView.as_view(), name="album-update"),
    path(
        "albums/<int:pk>/delete/", views.AlbumDeleteView.as_view(), name="album-delete"
    ),
    # Песни
    path("songs/", views.SongListView.as_view(), name="song-list"),
    path("songs/add/", views.SongCreateView.as_view(), name="song-create"),
    path("songs/<int:pk>/", views.SongDetailView.as_view(), name="song-detail"),
    path("songs/<int:pk>/edit/", views.SongUpdateView.as_view(), name="song-update"),
    path("songs/<int:pk>/delete/", views.SongDeleteView.as_view(), name="song-delete"),
    # Треклист
    path(
        "albums/<int:album_pk>/tracks/add/",
        views.AlbumTrackCreateView.as_view(),
        name="track-create",
    ),
    path(
        "tracks/<int:pk>/edit/",
        views.AlbumTrackUpdateView.as_view(),
        name="track-update",
    ),
    path(
        "tracks/<int:pk>/delete/",
        views.AlbumTrackDeleteView.as_view(),
        name="track-delete",
    ),
]
