from django import forms

from catalog.models import Album, AlbumTrack, Artist, Song


class ArtistForm(forms.ModelForm):
    class Meta:
        model = Artist
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"autofocus": True, "placeholder": "Queen"})
        }


class AlbumForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = ["title", "artist", "release_year"]
        widgets = {
            "title": forms.TextInput(
                attrs={"autofocus": True, "placeholder": "A Night at the Opera"}
            ),
            "release_year": forms.NumberInput(attrs={"placeholder": "1975"}),
        }


class SongForm(forms.ModelForm):
    class Meta:
        model = Song
        fields = ["title"]
        widgets = {
            "title": forms.TextInput(
                attrs={"autofocus": True, "placeholder": "Bohemian Rhapsody"}
            )
        }


class AlbumTrackForm(forms.ModelForm):
    class Meta:
        model = AlbumTrack
        fields = ["song", "track_number"]

    def __init__(self, *args, album: Album, **kwargs):
        super().__init__(*args, **kwargs)
        self.album = album
        self.instance.album = album
        self.fields["song"].queryset = Song.objects.all()
        self.fields["song"].empty_label = "— выберите песню —"
        if not self.instance.pk:
            self.fields["track_number"].initial = album.next_track_number()

    def clean(self):
        cleaned = super().clean()
        song = cleaned.get("song")
        number = cleaned.get("track_number")
        taken = AlbumTrack.objects.filter(album=self.album).exclude(pk=self.instance.pk)

        if number is not None and taken.filter(track_number=number).exists():
            self.add_error("track_number", f"Номер {number} уже занят в этом альбоме.")

        if song is not None and taken.filter(song=song).exists():
            self.add_error("song", f"Песня «{song.title}» уже есть в этом альбоме.")

        return cleaned


class CatalogSearchForm(forms.Form):
    """Единая форма поиска и фильтрации"""

    search = forms.CharField(
        required=False,
        label="Поиск",
        widget=forms.TextInput(
            attrs={"placeholder": "Название или имя…", "type": "search"}
        ),
    )
    artist = forms.ModelChoiceField(
        required=False,
        queryset=Artist.objects.all(),
        label="Исполнитель",
        empty_label="Все исполнители",
    )
    year = forms.IntegerField(
        required=False,
        label="Год",
        widget=forms.NumberInput(attrs={"placeholder": "1975"}),
    )
