# -*- coding: utf-8 -*-
from django.conf.urls import url

from fdadb.api import MedicationNamesListAPI, MedicationNDCsListAPI, MedicationStrengthsListAPI

urlpatterns = [
    url(r"^medications$", MedicationNamesListAPI.as_view(), name="fdadb-medications-names"),
    url(
        r"^medications/(?P<medication_name>[\w-]+)/strengths$",
        MedicationStrengthsListAPI.as_view(),
        name="fdadb-medications-strengths",
    ),
    url(
        r"^medications/(?P<medication_name>[\w-]+)/strengths/(?P<strength_id>[\d-]+)/ndcs$",
        MedicationNDCsListAPI.as_view(),
        name="fdadb-medications-ndcs",
    ),
]
