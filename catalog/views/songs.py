from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Prefetch
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from catalog.forms import SongForm
from catalog.models import AlbumTrack, Song
from catalog.views.base import SearchFormMixin


class SongListView(SearchFormMixin, ListView):
    model = Song
    template_name = "catalog/song_list.html"
    context_object_name = "songs"
    paginate_by = 50

    def get_queryset(self):
        queryset = Song.objects.annotate(
            album_count=Count("album_entries", distinct=True)
        ).order_by("title")
        query = self.search_param("search")
        if query:
            queryset = queryset.filter(title__icontains=query)
        return queryset


class SongDetailView(DetailView):
    model = Song
    template_name = "catalog/song_detail.html"
    context_object_name = "song"

    def get_queryset(self):
        return Song.objects.prefetch_related(
            Prefetch(
                "album_entries",
                queryset=AlbumTrack.objects.select_related("album__artist").order_by(
                    "album__release_year", "album__title"
                ),
            )
        )


class SongCreateView(SuccessMessageMixin, CreateView):
    model = Song
    form_class = SongForm
    template_name = "catalog/song_form.html"
    success_message = "Песня «%(title)s» добавлена."


class SongUpdateView(SuccessMessageMixin, UpdateView):
    model = Song
    form_class = SongForm
    template_name = "catalog/song_form.html"
    success_message = "Песня «%(title)s» обновлена."


class SongDeleteView(DeleteView):
    model = Song
    template_name = "catalog/confirm_delete.html"
    success_url = reverse_lazy("catalog:song-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_kind"] = "песню"
        context["consequence"] = (
            "Песня исчезнет из треклистов всех альбомов. Сами альбомы останутся."
        )
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Песня «{self.object.title}» удалена.")
        return super().form_valid(form)
