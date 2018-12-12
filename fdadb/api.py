# -*- coding: utf-8 -*-
from django.conf import settings
from rest_framework.generics import ListAPIView
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.permissions import AllowAny

from fdadb.es_search import EsSearchAPI
from fdadb.models import MedicationName, MedicationNDC, MedicationStrength
from fdadb.serializers import MedicationNameSerializer, MedicationNDCSerializer, MedicationStrengthSerializer

AUTOCOMPLETE_LIMIT = getattr(settings, "FDADB_AUTOCOMPLETE_LIMIT", 10)


class SearchMixin(object):
    def get_q_and_es_enabled(self):
        es_enabled = bool(getattr(settings, "ELASTICSEARCH_URL", None) and not getattr(settings, "TESTING", False))
        q = None
        if hasattr(self, "request"):
            if "q" in self.request.GET:
                q = self.request.GET["q"]
        return q, es_enabled


class MedicationNamesListAPI(ListAPIView, SearchMixin):
    permission_classes = (AllowAny,)
    # for now list of autocomplete results will be limited, so no pagination is needed
    # TODO: add ES pagination
    pagination_class = LimitOffsetPagination
    queryset = MedicationName.objects.all()
    serializer_class = MedicationNameSerializer
    ordering = ("name",)

    def get_queryset(self):
        q, es_enabled = self.get_q_and_es_enabled()
        if es_enabled:
            count, objects_list = EsSearchAPI().search_name(q, AUTOCOMPLETE_LIMIT)
            return objects_list
        else:
            queryset = super().get_queryset()
            if q:
                queryset = queryset.filter(name__icontains=q)[:AUTOCOMPLETE_LIMIT]
            return queryset


class MedicationStrengthsListAPI(ListAPIView, SearchMixin):
    # TODO: add filtering and use ES for the queryset (with pagination)
    permission_classes = (AllowAny,)
    pagination_class = PageNumberPagination
    queryset = MedicationStrength.objects.all()
    serializer_class = MedicationStrengthSerializer
    ordering = ("id",)

    def get_queryset(self):
        q, es_enabled = self.get_q_and_es_enabled()
        queryset = super().get_queryset().filter(medication_name__name=self.kwargs["medication_name"])
        if q:
            queryset = queryset.filter(strength__icontains=q)
        return queryset


class MedicationNDCsListAPI(ListAPIView, SearchMixin):
    # TODO: add filtering and use ES for the queryset (with pagination)
    permission_classes = (AllowAny,)
    pagination_class = PageNumberPagination
    queryset = MedicationNDC.objects.all()
    serializer_class = MedicationNDCSerializer
    ordering = ("id",)

    def get_queryset(self):
        q, es_enabled = self.get_q_and_es_enabled()
        queryset = super().get_queryset()
        queryset = queryset.filter(
            medication_strength__medication_name__name=self.kwargs["medication_name"],
            medication_strength_id=self.kwargs["strength_id"],
        )

        if q:
            queryset = queryset.filter(manufacturer__icontains=q)
        return queryset
