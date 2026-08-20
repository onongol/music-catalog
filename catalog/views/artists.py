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

from catalog.forms import ArtistForm
from catalog.models import Album, Artist
from catalog.views.base import SearchFormMixin


class ArtistListView(SearchFormMixin, ListView):
    model = Artist
    template_name = "catalog/artist_list.html"
    context_object_name = "artists"
    paginate_by = 25

    def get_queryset(self):
        queryset = Artist.objects.annotate(
            album_count=Count("albums", distinct=True)
        ).order_by("name")
        query = self.search_param("search")
        if query:
            queryset = queryset.filter(name__icontains=query)
        return queryset


class ArtistDetailView(DetailView):
    model = Artist
    template_name = "catalog/artist_detail.html"
    context_object_name = "artist"

    def get_queryset(self):
        return Artist.objects.prefetch_related(
            Prefetch(
                "albums",
                queryset=Album.objects.annotate(track_count=Count("tracks")).order_by(
                    "release_year", "title"
                ),
            )
        )


class ArtistCreateView(SuccessMessageMixin, CreateView):
    model = Artist
    form_class = ArtistForm
    template_name = "catalog/artist_form.html"
    success_message = "Исполнитель «%(name)s» добавлен."


class ArtistUpdateView(SuccessMessageMixin, UpdateView):
    model = Artist
    form_class = ArtistForm
    template_name = "catalog/artist_form.html"
    success_message = "Исполнитель «%(name)s» обновлён."


class ArtistDeleteView(DeleteView):
    model = Artist
    template_name = "catalog/confirm_delete.html"
    success_url = reverse_lazy("catalog:artist-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_kind"] = "исполнителя"
        context["consequence"] = (
            "Все альбомы исполнителя будут удалены. Песни останутся в каталоге."
        )
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Исполнитель «{self.object}» удалён.")
        return super().form_valid(form)
