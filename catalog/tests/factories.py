import factory

from catalog.models import Album, AlbumTrack, Artist, Song


class ArtistFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Artist
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Исполнитель {n}")


class AlbumFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Album

    title = factory.Sequence(lambda n: f"Альбом {n}")
    artist = factory.SubFactory(ArtistFactory)
    release_year = 1975


class SongFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Song

    title = factory.Sequence(lambda n: f"Песня {n}")


class AlbumTrackFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AlbumTrack

    album = factory.SubFactory(AlbumFactory)
    song = factory.SubFactory(SongFactory)
    track_number = factory.Sequence(lambda n: n + 1)
