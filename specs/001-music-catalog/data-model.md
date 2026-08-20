# Модель данных: 001-music-catalog

## Схема

```
┌─────────────────┐
│ Artist          │
│─────────────────│
│ id              │
│ name  (unique)  │
└────────┬────────┘
         │ 1
         │
         │ N          ┌──────────────────────────┐
┌────────▼────────┐   │ AlbumTrack               │   ┌─────────────────┐
│ Album           │ 1 │──────────────────────────│ N │ Song            │
│─────────────────│───│ id                       │───│─────────────────│
│ id              │ N │ album_id      → Album    │ 1 │ id              │
│ title           │   │ song_id       → Song     │   │ title           │
│ artist_id       │   │ track_number  (≥ 1)      │   │ created_at      │
│ release_year    │   └──────────────────────────┘   └─────────────────┘
│ created_at      │     unique (album, track_number)
└─────────────────┘     unique (album, song)
  unique (artist, title)
```

## Таблицы

### `catalog_artist`

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `id` | BigAutoField | PK |
| `name` | CharField(200) | UNIQUE, NOT NULL |
| `created_at` | DateTimeField | auto_now_add |

Сортировка по умолчанию: `name`.

### `catalog_album`

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `id` | BigAutoField | PK |
| `title` | CharField(200) | NOT NULL |
| `artist_id` | FK → `catalog_artist` | ON DELETE CASCADE, `related_name="albums"` |
| `release_year` | PositiveSmallIntegerField | CHECK 1860 ≤ year ≤ 2100 |
| `created_at` | DateTimeField | auto_now_add |

* `UniqueConstraint(artist, title)` — `unique_album_per_artist`
* `CheckConstraint` — `album_release_year_range`
* Индекс по `release_year` (фильтрация, FR-21)
* Сортировка по умолчанию: `artist__name`, `release_year`, `title`

### `catalog_song`

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `id` | BigAutoField | PK |
| `title` | CharField(200) | NOT NULL, индекс |
| `created_at` | DateTimeField | auto_now_add |

Название **не уникально**: разные песни могут называться одинаково
(«Intro», «Untitled»). Уникальность обеспечивается идентификатором.

### `catalog_albumtrack`

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `id` | BigAutoField | PK |
| `album_id` | FK → `catalog_album` | ON DELETE CASCADE, `related_name="tracks"` |
| `song_id` | FK → `catalog_song` | ON DELETE CASCADE, `related_name="album_entries"` |
| `track_number` | PositiveSmallIntegerField | MinValueValidator(1) |

* `UniqueConstraint(album, track_number)` — `unique_track_number_per_album`
* `UniqueConstraint(album, song)` — `unique_song_per_album`
* Сортировка по умолчанию: `album`, `track_number`

## Каскады удаления

| Удаляем | Последствие |
|---------|-------------|
| Artist | удаляются его Album → удаляются их AlbumTrack. **Song не затрагиваются** (FR-10) |
| Album | удаляются его AlbumTrack. Song не затрагиваются |
| Song | удаляются её AlbumTrack. Album не затрагиваются (FR-19) |
| AlbumTrack | не затрагивает ни Album, ни Song |

## Ключевой сценарий в терминах строк таблиц

```
catalog_artist      (1, "Queen")
catalog_album       (1, "A Night at the Opera", artist=1, 1975)
catalog_album       (2, "Greatest Hits",        artist=1, 1981)
catalog_song        (1, "Bohemian Rhapsody")

catalog_albumtrack  (1, album=1, song=1, track_number=11)
catalog_albumtrack  (2, album=2, song=1, track_number=1)
```

Одна строка в `catalog_song`, два разных номера. Ни одно ограничение не нарушено:
пары `(album, track_number)` и `(album, song)` уникальны в обеих строках.
