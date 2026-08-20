from catalog.views.albums import (
    AlbumCreateView,
    AlbumDeleteView,
    AlbumDetailView,
    AlbumListView,
    AlbumUpdateView,
)
from catalog.views.artists import (
    ArtistCreateView,
    ArtistDeleteView,
    ArtistDetailView,
    ArtistListView,
    ArtistUpdateView,
)
from catalog.views.base import HomeView, SearchFormMixin
from catalog.views.songs import (
    SongCreateView,
    SongDeleteView,
    SongDetailView,
    SongListView,
    SongUpdateView,
)
from catalog.views.tracks import (
    AlbumTrackCreateView,
    AlbumTrackDeleteView,
    AlbumTrackUpdateView,
)

__all__ = [
    "HomeView",
    "SearchFormMixin",
    "ArtistListView",
    "ArtistDetailView",
    "ArtistCreateView",
    "ArtistUpdateView",
    "ArtistDeleteView",
    "AlbumListView",
    "AlbumDetailView",
    "AlbumCreateView",
    "AlbumUpdateView",
    "AlbumDeleteView",
    "SongListView",
    "SongDetailView",
    "SongCreateView",
    "SongUpdateView",
    "SongDeleteView",
    "AlbumTrackCreateView",
    "AlbumTrackUpdateView",
    "AlbumTrackDeleteView",
]
