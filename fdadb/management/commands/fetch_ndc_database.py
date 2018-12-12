import csv
import zipfile
from collections import OrderedDict
from io import BytesIO, TextIOWrapper

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from fdadb.models import MedicationName, MedicationNDC, MedicationStrength

FDA_NDC_DATABASE_URL = getattr(
    settings, "FDA_NDC_DATABASE_URL", "https://www.accessdata.fda.gov/cder/ndctext.zip"
)


def strip_list_items(items):
    """Apply str.strip to all items in a list"""
    return list(map(str.strip, items))


class Command(BaseCommand):
    help = "Fetch the National Drug Codes and save the result to the database"

    def fetch_database_file(self):
        # fetch the zip file from FDA site
        response = requests.get(FDA_NDC_DATABASE_URL)
        response.raise_for_status()
        return response.content

    def get_products_data(self):
        # extract and read product.txt from the archive
        buffer = BytesIO()
        buffer.write(self.fetch_database_file())
        z = zipfile.ZipFile(buffer)

        with z.open("product.txt") as f:
            f = TextIOWrapper(f, encoding="cp1252")
            yield from csv.DictReader(f, delimiter="\t")

    def get_medication_strength_data(self, product_data):
        # some product does not provide substance name
        substance_name = product_data["SUBSTANCENAME"]
        if not substance_name:
            return {}

        active_substances = strip_list_items(substance_name.split(";"))
        substances_strength = strip_list_items(
            product_data["ACTIVE_NUMERATOR_STRENGTH"].split(";")
        )
        substances_units = strip_list_items(
            product_data["ACTIVE_INGRED_UNIT"].split(";")
        )
        return OrderedDict(
            (substance, {"strength": strength, "unit": unit})
            for substance, strength, unit in zip(
                active_substances, substances_strength, substances_units
            )
        )

    def handle(self, *args, **options):
        # each product has following fields:
        # * PROPRIETARYNAME - name of the drug
        # * PROPRIETARYNAMESUFFIX - some drugs has suffix in their names
        # * SUBSTANCENAME - names of the substances in the drug, e.g.: CLINDAMYCIN PHOSPHATE; TRETINOIN
        # * ACTIVE_NUMERATOR_STRENGTH - strengths of the substances, e.g.: 12; .25
        # * ACTIVE_INGRED_UNIT - units for the strengths e.g.: mg/g; mg/g

        cache = {}

        def cached_get_or_create(key, model, defaults=None, **kwargs):
            try:
                return cache[key], False
            except KeyError:
                obj, created = model.objects.get_or_create(defaults=defaults, **kwargs)
                cache[key] = obj
                return obj, created

        products_data = self.get_products_data()
        skipped = 0
        for i, product in enumerate(products_data):
            if (i % 100) == 0:
                print("\rrow {}".format(i), end="", flush=True)
            if product["NDC_EXCLUDE_FLAG"] != "N":
                skipped += 1
                continue
            product_name = "{} {}".format(
                product["PROPRIETARYNAME"].strip(),
                product["PROPRIETARYNAMESUFFIX"].strip(),
            ).strip()
            strength_data = self.get_medication_strength_data(product)
            medication_name, created = cached_get_or_create(
                "name:{}".format(product_name),
                MedicationName,
                name=product_name,
                defaults={"active_substances": list(strength_data.keys())},
            )
            medication_strength, created = cached_get_or_create(
                "strength:{}-{}".format(medication_name.name, strength_data),
                MedicationStrength,
                medication_name=medication_name,
                strength=strength_data,
            )
            ndc = product["PRODUCTNDC"]
            cached_get_or_create(
                "ndc:{}".format(ndc),
                MedicationNDC,
                ndc=ndc,
                defaults={
                    "medication_strength": medication_strength,
                    "manufacturer": product["LABELERNAME"],
                },
            )
        print("\rDone.  {} rows, {} excluded drugs".format(i, skipped))
