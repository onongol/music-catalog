from rest_framework import serializers

from catalog.models import Album, AlbumTrack, Artist, Song


class AnnotatedCountMixin:
    """Берёт счётчик из аннотации queryset-а, а если её нет — считает запросом.

    Списки аннотируются во вьюсете, но ответ на POST отдаёт свежий
    объект без аннотаций — для него нужен запасной путь.
    """

    @staticmethod
    def _count(obj, attr: str, related: str) -> int:
        value = getattr(obj, attr, None)
        return value if value is not None else getattr(obj, related).count()


class AlbumBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        fields = ["id", "title", "release_year"]


class TrackInAlbumSerializer(serializers.ModelSerializer):
    """Строка треклиста внутри альбома."""

    song_title = serializers.CharField(source="song.title", read_only=True)

    class Meta:
        model = AlbumTrack
        fields = ["id", "track_number", "song", "song_title"]


class SongAppearanceSerializer(serializers.ModelSerializer):
    """Вхождение песни в альбом — с номером именно в этом альбоме."""

    album_title = serializers.CharField(source="album.title", read_only=True)
    artist_name = serializers.CharField(source="album.artist.name", read_only=True)
    release_year = serializers.IntegerField(source="album.release_year", read_only=True)

    class Meta:
        model = AlbumTrack
        fields = ["album", "album_title", "artist_name", "release_year", "track_number"]


class ArtistSerializer(AnnotatedCountMixin, serializers.ModelSerializer):
    album_count = serializers.SerializerMethodField()
    albums = AlbumBriefSerializer(many=True, read_only=True)

    class Meta:
        model = Artist
        fields = ["id", "name", "album_count", "albums"]

    def get_album_count(self, obj) -> int:
        return self._count(obj, "album_count", "albums")


class AlbumSerializer(AnnotatedCountMixin, serializers.ModelSerializer):
    artist_name = serializers.CharField(source="artist.name", read_only=True)
    track_count = serializers.SerializerMethodField()
    tracks = TrackInAlbumSerializer(many=True, read_only=True)

    class Meta:
        model = Album
        fields = [
            "id",
            "title",
            "artist",
            "artist_name",
            "release_year",
            "track_count",
            "tracks",
        ]
        # Автовалидаторы, выведенные из UniqueConstraint модели, отключены:
        # сообщения об ошибках задаются явно в validate().
        validators = []

    def get_track_count(self, obj) -> int:
        return self._count(obj, "track_count", "tracks")

    def validate(self, attrs):
        artist = attrs.get("artist", getattr(self.instance, "artist", None))
        title = attrs.get("title", getattr(self.instance, "title", None))
        clash = Album.objects.filter(artist=artist, title=title)
        if self.instance is not None:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise serializers.ValidationError(
                f"У исполнителя «{artist}» уже есть альбом «{title}»."
            )
        return attrs


class SongSerializer(AnnotatedCountMixin, serializers.ModelSerializer):
    album_count = serializers.SerializerMethodField()
    appears_on = SongAppearanceSerializer(
        source="album_entries", many=True, read_only=True
    )

    class Meta:
        model = Song
        fields = ["id", "title", "album_count", "appears_on"]

    def get_album_count(self, obj) -> int:
        return self._count(obj, "album_count", "album_entries")


class AlbumTrackSerializer(serializers.ModelSerializer):
    """Вхождение песни в альбом."""

    song_title = serializers.CharField(source="song.title", read_only=True)
    album_title = serializers.CharField(source="album.title", read_only=True)

    class Meta:
        model = AlbumTrack
        fields = ["id", "album", "album_title", "song", "song_title", "track_number"]
        validators = []

    def validate(self, attrs):
        album = attrs.get("album", getattr(self.instance, "album", None))
        song = attrs.get("song", getattr(self.instance, "song", None))
        number = attrs.get("track_number", getattr(self.instance, "track_number", None))

        siblings = AlbumTrack.objects.filter(album=album)
        if self.instance is not None:
            siblings = siblings.exclude(pk=self.instance.pk)

        if siblings.filter(track_number=number).exists():
            raise serializers.ValidationError(
                f"Номер {number} уже занят в этом альбоме."
            )
        if siblings.filter(song=song).exists():
            raise serializers.ValidationError("Эта песня уже есть в альбоме.")

        return attrs
