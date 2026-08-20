from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, UpdateView

from catalog.forms import AlbumTrackForm
from catalog.models import Album, AlbumTrack


class AlbumTrackCreateView(SuccessMessageMixin, CreateView):
    model = AlbumTrack
    form_class = AlbumTrackForm
    template_name = "catalog/track_form.html"
    success_message = "Песня добавлена в альбом."

    @property
    def album(self) -> Album:
        if not hasattr(self, "_album"):
            self._album = get_object_or_404(
                Album.objects.select_related("artist"), pk=self.kwargs["album_pk"]
            )
        return self._album

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["album"] = self.album
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["album"] = self.album
        return context

    def get_success_url(self):
        return reverse("catalog:album-detail", args=[self.album.pk])


class AlbumTrackUpdateView(SuccessMessageMixin, UpdateView):
    model = AlbumTrack
    form_class = AlbumTrackForm
    template_name = "catalog/track_form.html"
    success_message = "Трек обновлён."

    def get_queryset(self):
        return AlbumTrack.objects.select_related("album__artist", "song")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["album"] = self.object.album
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["album"] = self.object.album
        return context

    def get_success_url(self):
        return reverse("catalog:album-detail", args=[self.object.album_id])


class AlbumTrackDeleteView(DeleteView):
    model = AlbumTrack
    template_name = "catalog/confirm_delete.html"

    def get_queryset(self):
        return AlbumTrack.objects.select_related("album__artist", "song")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_kind"] = "трек"
        context["consequence"] = (
            "Песня будет убрана из этого альбома, но останется в каталоге "
            "и в треклистах других альбомов."
        )
        return context

    def form_valid(self, form):
        messages.success(
            self.request, f"Песня «{self.object.song.title}» убрана из альбома."
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("catalog:album-detail", args=[self.object.album_id])
