# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from fdadb.es_search import EsSearchAPI


class Command(BaseCommand):
    help = "FDA DB: Create ElasticSearch Index"

    def add_arguments(self, parser):
        parser.add_argument(
            "--drop_indexes",
            action="store_true",
            dest="drop_indexes",
            default=False,
            help="Should indexes be removed before reindexing?",
        )

    def handle(self, *args, **kwargs):
        drop_indexes = kwargs.get("drop_indexes")

        EsSearchAPI().index_medications(drop_indexes=drop_indexes)
