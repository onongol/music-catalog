from django.contrib import admin
from django.db.models import Count

from catalog.models import Album, AlbumTrack, Artist, Song


class AlbumInline(admin.TabularInline):
    model = Album
    extra = 0
    fields = ["title", "release_year"]
    show_change_link = True


class AlbumTrackInline(admin.TabularInline):
    """Треклист прямо в карточке альбома — основной способ правки в админке."""

    model = AlbumTrack
    extra = 1
    fields = ["track_number", "song"]
    ordering = ["track_number"]
    autocomplete_fields = ["song"]


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ["name", "album_count"]
    search_fields = ["name"]
    inlines = [AlbumInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_album_count=Count("albums"))

    @admin.display(description="альбомов", ordering="_album_count")
    def album_count(self, obj):
        return obj._album_count


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ["title", "artist", "release_year", "track_count"]
    list_filter = ["release_year", "artist"]
    search_fields = ["title", "artist__name"]
    autocomplete_fields = ["artist"]
    inlines = [AlbumTrackInline]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("artist")
            .annotate(_track_count=Count("tracks"))
        )

    @admin.display(description="треков", ordering="_track_count")
    def track_count(self, obj):
        return obj._track_count


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ["title", "album_count"]
    search_fields = ["title"]

    def get_queryset(self, request):
        return (
            super().get_queryset(request).annotate(_album_count=Count("album_entries"))
        )

    @admin.display(description="в альбомах", ordering="_album_count")
    def album_count(self, obj):
        return obj._album_count


@admin.register(AlbumTrack)
class AlbumTrackAdmin(admin.ModelAdmin):
    list_display = ["album", "track_number", "song"]
    list_filter = ["album__artist"]
    search_fields = ["album__title", "song__title"]
    autocomplete_fields = ["album", "song"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("album__artist", "song")


admin.site.site_header = "Каталог музыкальных альбомов"
admin.site.site_title = "Music Catalog"
admin.site.index_title = "Управление каталогом"
