# -*- coding: utf-8 -*-
from django.conf import settings
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from fdadb.es_search import EsSearchAPI
from fdadb.models import MedicationName, MedicationStrength, MedicationNDC
from fdadb.serializers import MedicationNameSerializer, MedicationStrengthSerializer, MedicationNDCSerializer


class SearchMixin(object):
    def get_q_ans_es_enabled(self):
        es_enabled = bool(getattr(settings, "ELASTICSEARCH_URL", None) and not getattr(settings, "TESTING", False))
        q = None
        if hasattr(self, "request"):
            if "q" in self.request.GET:
                q = self.request.GET["q"]
        return q, es_enabled


class MedicationNamesListAPI(ListAPIView, SearchMixin):
    permission_classes = (AllowAny,)
    pagination_class = PageNumberPagination
    queryset = MedicationName.objects.all()
    serializer_class = MedicationNameSerializer
    ordering = ("name",)

    def get_queryset(self):
        q, es_enabled = self.get_q_ans_es_enabled()
        if es_enabled:
            count, objects_list = EsSearchAPI().search_name(q)  # FIXME: return count on paginator
            return objects_list
        else:
            queryset = super().get_queryset()
            if q:
                queryset = queryset.filter(name__icontains=q)
            return queryset


class MedicationStrengthsListAPI(ListAPIView, SearchMixin):
    permission_classes = (AllowAny,)
    pagination_class = PageNumberPagination
    queryset = MedicationStrength.objects.all()
    serializer_class = MedicationStrengthSerializer
    ordering = ("id",)

    def get_queryset(self):
        q, es_enabled = self.get_q_ans_es_enabled()
        if es_enabled:
            count, objects_list = EsSearchAPI().search_strength(
                self.kwargs["medication_name"], q
            )  # FIXME: return count on paginator
            return objects_list
        else:
            queryset = super().get_queryset().filter(medication_name__name=self.kwargs["medication_name"])
            if q:
                queryset = queryset.filter(strength__icontains=q)
            return queryset


class MedicationNDCsListAPI(ListAPIView, SearchMixin):
    permission_classes = (AllowAny,)
    pagination_class = PageNumberPagination
    queryset = MedicationNDC.objects.all()
    serializer_class = MedicationNDCSerializer
    ordering = ("id",)

    def get_queryset(self):
        q, es_enabled = self.get_q_ans_es_enabled()
        if es_enabled:
            count, objects_list = EsSearchAPI().search_ndc(
                self.kwargs["medication_name"], self.kwargs["strength_id"], q
            )  # FIXME: return count on paginator
            return objects_list
        else:
            queryset = (
                super()
                .get_queryset()
                .filter(
                    medication_strength__medication_name__name=self.kwargs["medication_name"],
                    medication_strength_id=self.kwargs["strength_id"],
                )
            )
            if q:
                queryset = queryset.filter(manufacturer__icontains=q)
            return queryset
