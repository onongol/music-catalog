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

from catalog.forms import AlbumForm
from catalog.models import Album, AlbumTrack
from catalog.views.base import SearchFormMixin


class AlbumListView(SearchFormMixin, ListView):
    model = Album
    template_name = "catalog/album_list.html"
    context_object_name = "albums"
    paginate_by = 25

    def get_queryset(self):
        queryset = (
            Album.objects.select_related("artist")
            .annotate(track_count=Count("tracks"))
            .order_by("artist__name", "release_year", "title")
        )
        query = self.search_param("search")
        artist = self.search_param("artist")
        year = self.search_param("year")
        if query:
            queryset = queryset.filter(title__icontains=query)
        if artist:
            queryset = queryset.filter(artist=artist)
        if year:
            queryset = queryset.filter(release_year=year)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_filters"] = True
        return context


class AlbumDetailView(DetailView):
    model = Album
    template_name = "catalog/album_detail.html"
    context_object_name = "album"

    def get_queryset(self):
        return Album.objects.select_related("artist").prefetch_related(
            Prefetch(
                "tracks",
                # Счётчик альбомов песни считается тем же запросом, что и треклист,
                # иначе шаблон сделал бы запрос на каждую строку.
                queryset=AlbumTrack.objects.select_related("song")
                .annotate(song_album_count=Count("song__album_entries", distinct=True))
                .order_by("track_number"),
            )
        )


class AlbumCreateView(SuccessMessageMixin, CreateView):
    model = Album
    form_class = AlbumForm
    template_name = "catalog/album_form.html"
    success_message = "Альбом «%(title)s» добавлен."

    def get_initial(self):
        initial = super().get_initial()
        artist_id = self.request.GET.get("artist")
        if artist_id:
            initial["artist"] = artist_id
        return initial


class AlbumUpdateView(SuccessMessageMixin, UpdateView):
    model = Album
    form_class = AlbumForm
    template_name = "catalog/album_form.html"
    success_message = "Альбом «%(title)s» обновлён."


class AlbumDeleteView(DeleteView):
    model = Album
    template_name = "catalog/confirm_delete.html"
    success_url = reverse_lazy("catalog:album-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_kind"] = "альбом"
        context["consequence"] = (
            "Треклист будет удалён. Сами песни останутся в каталоге."
        )
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Альбом «{self.object.title}» удалён.")
        return super().form_valid(form)
