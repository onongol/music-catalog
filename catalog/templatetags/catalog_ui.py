"""Данные для повторяющихся кусков интерфейса.

Разметка живёт в catalog/templates/catalog/components/, здесь только списки,
по которым шаблоны проходят циклом: в языке шаблонов Django нет литералов
списка, а без цикла классы Tailwind пришлось бы копировать на каждый пункт.
"""

from django import template
from django.urls import reverse

register = template.Library()


@register.inclusion_tag("catalog/components/nav.html")
def main_nav():
    """Пункты главного меню."""
    return {
        "items": [
            {"label": "Исполнители", "url": reverse("catalog:artist-list")},
            {"label": "Альбомы", "url": reverse("catalog:album-list")},
            {"label": "Песни", "url": reverse("catalog:song-list")},
            {"label": "API", "url": "/api/"},
            {"label": "Админка", "url": "/admin/"},
        ]
    }


@register.simple_tag
def table_columns(*labels):
    """Колонки для components/table.html.

    «Год:right» — заголовок выравнивается по правому краю, пустая строка —
    служебная колонка без заголовка (ссылки правки и удаления).
    """
    columns = []
    for label in labels:
        text, _, align = label.partition(":")
        columns.append({"label": text, "right": align == "right"})
    return columns
