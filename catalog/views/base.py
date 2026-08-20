from django.db.models import Count
from django.urls import reverse
from django.views.generic import TemplateView

from catalog.forms import CatalogSearchForm
from catalog.models import Album, AlbumTrack, Artist, Song


class HomeView(TemplateView):
    """Сводка каталога и точки входа в разделы."""

    template_name = "catalog/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            artist_count=Artist.objects.count(),
            album_count=Album.objects.count(),
            song_count=Song.objects.count(),
            track_count=AlbumTrack.objects.count(),
            latest_albums=Album.objects.select_related("artist").order_by(
                "-created_at"
            )[:5],
            multi_album_songs=(
                Song.objects.annotate(album_count=Count("album_entries"))
                .filter(album_count__gt=1)
                .order_by("-album_count", "title")[:5]
            ),
        )
        # Плитки сводки описаны списком: разметка карточки лежит в одном шаблоне,
        # который главная проходит циклом.
        context["stats"] = [
            {
                "value": context["artist_count"],
                "label": "исполнителей",
                "url": reverse("catalog:artist-list"),
            },
            {
                "value": context["album_count"],
                "label": "альбомов",
                "url": reverse("catalog:album-list"),
            },
            {
                "value": context["song_count"],
                "label": "песен",
                "url": reverse("catalog:song-list"),
            },
            {"value": context["track_count"], "label": "треков в альбомах"},
        ]
        return context


class SearchFormMixin:
    """Добавляет форму поиска в контекст и хранит очищенные параметры."""

    def get_search_form(self) -> CatalogSearchForm:
        if not hasattr(self, "_search_form"):
            self._search_form = CatalogSearchForm(self.request.GET or None)
            self._search_form.is_valid()
        return self._search_form

    def search_param(self, name):
        form = self.get_search_form()
        return form.cleaned_data.get(name) if form.is_bound else None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = self.get_search_form()
        return context
