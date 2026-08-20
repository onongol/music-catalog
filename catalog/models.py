from datetime import date

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

MIN_RELEASE_YEAR = 1860
MAX_RELEASE_YEAR = 2100


def validate_release_year(value: int) -> None:
    upper = date.today().year + 1
    if value < MIN_RELEASE_YEAR or value > upper:
        raise ValidationError(
            "Год выпуска должен быть между %(min)s и %(max)s.",
            params={"min": MIN_RELEASE_YEAR, "max": upper},
        )


class Artist(models.Model):
    name = models.CharField("имя", max_length=200, unique=True)
    created_at = models.DateTimeField("добавлен", auto_now_add=True)

    class Meta:
        verbose_name = "исполнитель"
        verbose_name_plural = "исполнители"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("catalog:artist-detail", args=[self.pk])


class Album(models.Model):
    title = models.CharField("название", max_length=200)
    artist = models.ForeignKey(
        Artist,
        verbose_name="исполнитель",
        on_delete=models.CASCADE,
        related_name="albums",
    )
    release_year = models.PositiveSmallIntegerField(
        "год выпуска",
        validators=[MinValueValidator(MIN_RELEASE_YEAR), validate_release_year],
    )
    created_at = models.DateTimeField("добавлен", auto_now_add=True)

    class Meta:
        verbose_name = "альбом"
        verbose_name_plural = "альбомы"
        ordering = ["artist__name", "release_year", "title"]
        constraints = [
            models.UniqueConstraint(
                fields=["artist", "title"],
                name="unique_album_per_artist",
                violation_error_message="У этого исполнителя уже есть альбом с таким названием.",
            ),
            models.CheckConstraint(
                condition=models.Q(release_year__gte=MIN_RELEASE_YEAR)
                & models.Q(release_year__lte=MAX_RELEASE_YEAR),
                name="album_release_year_range",
                violation_error_message="Год выпуска вне допустимого диапазона.",
            ),
        ]
        indexes = [models.Index(fields=["release_year"])]

    def __str__(self) -> str:
        return f"{self.artist.name} — {self.title} ({self.release_year})"

    def get_absolute_url(self) -> str:
        return reverse("catalog:album-detail", args=[self.pk])

    def next_track_number(self) -> int:
        """Первый свободный номер в конце треклиста — подсказка для формы."""
        last = self.tracks.aggregate(models.Max("track_number"))["track_number__max"]
        return (last or 0) + 1


class Song(models.Model):
    """
    Существует независимо от альбомов: удаление альбома не удаляет песню,
    а одна песня может входить в любое число альбомов.
    """

    title = models.CharField("название", max_length=200, db_index=True)
    created_at = models.DateTimeField("добавлена", auto_now_add=True)

    class Meta:
        verbose_name = "песня"
        verbose_name_plural = "песни"
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("catalog:song-detail", args=[self.pk])


class AlbumTrack(models.Model):
    """
    Отдельная сущность, а не техническая таблица связи: номер трека —
    свойство пары альбом + песня, поэтому песня может быть
    треком №11 в альбоме 1 и треком №1 в альбоме 2.
    """

    album = models.ForeignKey(
        Album,
        verbose_name="альбом",
        on_delete=models.CASCADE,
        related_name="tracks",
    )
    song = models.ForeignKey(
        Song,
        verbose_name="песня",
        on_delete=models.CASCADE,
        related_name="album_entries",
    )
    track_number = models.PositiveSmallIntegerField(
        "порядковый номер",
        validators=[MinValueValidator(1)],
    )

    class Meta:
        verbose_name = "трек"
        verbose_name_plural = "треки"
        ordering = ["album", "track_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["album", "track_number"],
                name="unique_track_number_per_album",
                violation_error_message="Этот номер уже занят в альбоме.",
            ),
            models.UniqueConstraint(
                fields=["album", "song"],
                name="unique_song_per_album",
                violation_error_message="Эта песня уже есть в альбоме.",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.album.title}: {self.track_number}. {self.song.title}"

    def get_absolute_url(self) -> str:
        return reverse("catalog:album-detail", args=[self.album_id])
