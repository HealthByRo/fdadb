# -*- coding: utf-8 -*-
from drf_tweaks.serializers import ModelSerializer
from rest_framework.fields import CharField

from fdadb.models import MedicationName, MedicationNDC, MedicationStrength


class JSONField(CharField):
    type_name = "JSONField"

    def to_internal_value(self, data):
        return data

    def to_representation(self, value):
        return value


class MedicationNameSerializer(ModelSerializer):
    active_substances = JSONField(read_only=True)

    class Meta:
        model = MedicationName
        fields = ["name", "active_substances"]


class MedicationStrengthSerializer(ModelSerializer):
    active_substances = JSONField(read_only=True)
    strength = JSONField(read_only=True)

    class Meta:
        model = MedicationStrength
        fields = ["name", "active_substances", "strength"]


class MedicationNDCSerializer(ModelSerializer):
    active_substances = JSONField(read_only=True)
    strength = JSONField(read_only=True)

    class Meta:
        model = MedicationNDC
        fields = ["name", "active_substances", "strength", "manufacturer", "ndc"]
