# Контракт REST API: 001-music-catalog

Базовый префикс: `/api/`. Формат: JSON. Аутентификация не требуется (см.
допущение 3 в `plan.md`). Просматриваемая в браузере версия доступна по тому же
адресу (FR-26).

## Ресурсы

| Метод | Путь | Действие |
|-------|------|----------|
| GET / POST | `/api/artists/` | список / создание |
| GET / PUT / PATCH / DELETE | `/api/artists/{id}/` | чтение / изменение / удаление |
| GET / POST | `/api/albums/` | список / создание |
| GET / PUT / PATCH / DELETE | `/api/albums/{id}/` | чтение / изменение / удаление |
| GET / POST | `/api/songs/` | список / создание |
| GET / PUT / PATCH / DELETE | `/api/songs/{id}/` | чтение / изменение / удаление |
| GET / POST | `/api/tracks/` | список / добавление песни в альбом |
| GET / PUT / PATCH / DELETE | `/api/tracks/{id}/` | чтение / изменение / удаление трека |

## Параметры запроса

| Ресурс | Параметр | Пример |
|--------|----------|--------|
| artists | `search` | `/api/artists/?search=queen` |
| albums | `artist`, `release_year`, `search`, `ordering` | `/api/albums/?artist=1&release_year=1975` |
| songs | `search` | `/api/songs/?search=rhapsody` |
| tracks | `album`, `song` | `/api/tracks/?album=1` |

## Представления

**Исполнитель**

```json
{
  "id": 1,
  "name": "Queen",
  "album_count": 2,
  "albums": [
    { "id": 1, "title": "A Night at the Opera", "release_year": 1975 },
    { "id": 2, "title": "Greatest Hits", "release_year": 1981 }
  ]
}
```

**Альбом** (FR-24 — вложенный треклист)

```json
{
  "id": 1,
  "title": "A Night at the Opera",
  "artist": 1,
  "artist_name": "Queen",
  "release_year": 1975,
  "track_count": 2,
  "tracks": [
    { "id": 5, "track_number": 1,  "song": 7, "song_title": "Death on Two Legs" },
    { "id": 6, "track_number": 11, "song": 1, "song_title": "Bohemian Rhapsody" }
  ]
}
```

При записи передаётся только `artist` (id); поля `artist_name`, `track_count`,
`tracks` доступны на чтение.

**Песня** (FR-18 — все вхождения с номерами)

```json
{
  "id": 1,
  "title": "Bohemian Rhapsody",
  "album_count": 2,
  "appears_on": [
    { "album": 1, "album_title": "A Night at the Opera", "artist_name": "Queen", "release_year": 1975, "track_number": 11 },
    { "album": 2, "album_title": "Greatest Hits",        "artist_name": "Queen", "release_year": 1981, "track_number": 1 }
  ]
}
```

**Трек**

```json
{ "id": 6, "album": 1, "song": 1, "song_title": "Bohemian Rhapsody", "album_title": "A Night at the Opera", "track_number": 11 }
```

## Ошибки (FR-25)

Занятый номер трека — `400 Bad Request`:

```json
{ "non_field_errors": ["Номер 3 уже занят в этом альбоме."] }
```

Повторное добавление песни в альбом — `400 Bad Request`:

```json
{ "non_field_errors": ["Эта песня уже есть в альбоме."] }
```

Некорректный год — `400 Bad Request`:

```json
{ "release_year": ["Год выпуска должен быть между 1860 и 2027."] }
```

Прочие коды: `404` — объект не найден, `405` — метод не разрешён.
