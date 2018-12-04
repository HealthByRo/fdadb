# -*- coding: utf-8 -*-
import json

from django.conf import settings
from elasticsearch import Elasticsearch

from fdadb.models import MedicationName, MedicationNDC, MedicationStrength


class EsSearchAPI(object):
    def __init__(self, *args, **kwargs):
        es_url = getattr(settings, "ELASTICSEARCH_URL", None)
        if es_url is None:
            raise Exception("ELASTICSEARCH_URL not configured in settings")
        self.es = Elasticsearch([settings.ELASTICSEARCH_URL])

    def create_indexes(self):
        self.es.indices.create(
            index="fda_medications_names",
            ignore=[400],  # ignore 400, so it ignores already existing
            body={
                "settings": {
                    "analysis": {
                        "filter": {"autocomplete_filter": {"type": "edge_ngram", "min_gram": 1, "max_gram": 20}},
                        "analyzer": {
                            "autocomplete": {
                                "type": "custom",
                                "tokenizer": "standard",
                                "filter": ["lowercase", "autocomplete_filter"],
                            }
                        },
                    }
                },
                "mappings": {"medication_name": {"properties": {"name": {"type": "text", "analyzer": "autocomplete"}}}},
            },
        )
        self.es.indices.create(
            index="fda_medications_strengths",
            ignore=[400],  # ignore 400, so it ignores already existing
            body={
                "settings": {
                    "analysis": {
                        "filter": {"autocomplete_filter": {"type": "edge_ngram", "min_gram": 1, "max_gram": 20}},
                        "analyzer": {
                            "autocomplete": {
                                "type": "custom",
                                "tokenizer": "standard",
                                "filter": ["lowercase", "autocomplete_filter"],
                            }
                        },
                    }
                },
                "mappings": {
                    "medication_strength": {
                        "properties": {
                            "name": {"type": "keyword"},
                            "strength_search_string": {"type": "text", "analyzer": "autocomplete"},
                        }
                    }
                },
            },
        )
        self.es.indices.create(
            index="fda_medications_ndcs",
            ignore=[400],  # ignore 400, so it ignores already existing
            body={
                "settings": {
                    "analysis": {
                        "filter": {"autocomplete_filter": {"type": "edge_ngram", "min_gram": 1, "max_gram": 20}},
                        "analyzer": {
                            "autocomplete": {
                                "type": "custom",
                                "tokenizer": "standard",
                                "filter": ["lowercase", "autocomplete_filter"],
                            }
                        },
                    }
                },
                "mappings": {
                    "medication_ndc": {
                        "properties": {
                            "name": {"type": "keyword"},
                            "strength_id": {"type": "long"},
                            "manufacturer": {"type": "text", "analyzer": "autocomplete"},
                        }
                    }
                },
            },
        )

    def drop_indexes(self):
        self.es.indices.delete(index="fda_medications_names", ignore=[400, 404])
        self.es.indices.delete(index="fda_medications_strengths", ignore=[400, 404])
        self.es.indices.delete(index="fda_medications_ndcs", ignore=[400, 404])

    @classmethod
    def _get_strength_search_string(cls, strength):
        return ", ".join("{} {} {}".format(key, value["strength"], value["unit"]) for key, value in strength.items())

    def index_medications(self, drop_indexes=False):
        if drop_indexes:
            self.drop_indexes()
        self.create_indexes()

        for medication_name in MedicationName.objects.all():
            doc = {"name": medication_name.name, "active_substances": medication_name.active_substances}
            self.es.index(index="fda_medications_names", doc_type="medication_name", id=medication_name.name, body=doc)

        for medication_strength in MedicationStrength.objects.select_related("medication_name").all():
            doc = {
                "name": medication_strength.medication_name.name,
                "active_substances": json.dumps(medication_strength.medication_name.active_substances),
                "strength": json.dumps(medication_strength.strength),
                "strength_search_string": self._get_strength_search_string(medication_strength.strength),
            }
            self.es.index(
                index="fda_medications_strengths", doc_type="medication_strength", id=medication_strength.id, body=doc
            )

        for medication_ndc in MedicationNDC.objects.select_related(
            "medication_strength", "medication_strength__medication_name"
        ).all():
            doc = {
                "name": medication_ndc.medication_strength.medication_name.name,
                "active_substances": json.dumps(medication_ndc.medication_strength.medication_name.active_substances),
                "strength": json.dumps(medication_ndc.medication_strength.strength),
                "strength_id": medication_ndc.medication_strength_id,
                "ndc": medication_ndc.ndc,
                "manufacturer": medication_ndc.manufacturer,
            }
            self.es.index(index="fda_medications_ndcs", doc_type="medication_ndc", id=medication_ndc.id, body=doc)

    @classmethod
    def _format_response(cls, response):
        count, results = response["hits"]["total"], [x["_source"] for x in response["hits"]["hits"]]
        for item in results:
            for key in ("strength", "active_substances"):
                if key in item and isinstance(item[key], str):
                    item[key] = json.loads(item[key])
        return count, results

    def search_name(self, name_search_string, size=10):
        if not name_search_string:
            body = {"query": {"match_all": {}}, "size": size}
        else:
            body = {"query": {"match": {"name": name_search_string}}, "size": size}
        response = self.es.search(index="fda_medications_names", body=body)
        return self._format_response(response)

    def search_strength(self, name, strength_search_string):
        body = {"size": 10, "query": {"bool": {"filter": {"term": {"name": name}}}}}
        if strength_search_string:
            body["query"]["bool"]["must"] = {"match": {"strength_search_string": strength_search_string}}
        response = self.es.search(index="fda_medications_strengths", body=body)
        return self._format_response(response)

    def search_ndc(self, name, strength_id, manufacturer_search_string):
        body = {
            "size": 10,
            "query": {"bool": {"filter": [{"term": {"name": name}}, {"term": {"strength_id": strength_id}}]}},
        }
        if manufacturer_search_string:
            body["query"]["bool"]["must"] = {"match": {"manufacturer": manufacturer_search_string}}
        response = self.es.search(index="fda_medications_ndcs", body=body)
        return self._format_response(response)
