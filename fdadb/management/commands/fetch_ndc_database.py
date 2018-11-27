import zipfile
from io import BytesIO

import pandas
import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from fdadb.models import MedicationName, MedicationNDC, MedicationStrength

FDA_NDC_DATABASE_URL = getattr(settings, "FDA_NDC_DATABASE_URL", "https://www.accessdata.fda.gov/cder/ndctext.zip")


def strip_list_items(items):
    """Apply str.strip to all items in a list"""
    return list(map(str.strip, items))


# TODO: optimize and add tests
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
        products_data = pandas.read_table(z.open("product.txt"), encoding="cp1252",
                                          keep_default_na=False, dtype=str).to_dict("records")
        z.close()
        return products_data

    def get_medication_strength_data(self, product_data):
        # some product does not provide substance name
        substance_name = product_data["SUBSTANCENAME"]
        if not substance_name:
            return {}

        active_substances = strip_list_items(substance_name.split(";"))
        substances_strength = strip_list_items(product_data["ACTIVE_NUMERATOR_STRENGTH"].split(";"))
        substances_units = strip_list_items(product_data["ACTIVE_INGRED_UNIT"].split(";"))
        return {
            active_substances[i]: {
                "strength": substances_strength[i], "unit": substances_units[i]
            } for i in range(len(active_substances))
        }

    def handle(self, *args, **options):
        # each product has following fields:
        # * PROPRIETARYNAME - name of the drug
        # * PROPRIETARYNAMESUFFIX - some drugs has suffix in their names
        # * SUBSTANCENAME - names of the substances in the drug, e.g.: CLINDAMYCIN PHOSPHATE; TRETINOIN
        # * ACTIVE_NUMERATOR_STRENGTH - strengths of the substances, e.g.: 12; .25
        # * ACTIVE_INGRED_UNIT - units for the strengths e.g.: mg/g; mg/g
        products_data = self.get_products_data()
        for product in products_data:
            print("Parsing: ", product["PROPRIETARYNAME"], product["PRODUCTNDC"])
            if product["NDC_EXCLUDE_FLAG"] != "N":
                print("Skipping excluded drug:", product["PROPRIETARYNAME"], product["PRODUCTNDC"])
                continue
            product_name = "{} {}".format(
                product["PROPRIETARYNAME"].strip(), product["PROPRIETARYNAMESUFFIX"].strip()).strip()
            strength_data = self.get_medication_strength_data(product)
            medication_name, created = MedicationName.objects.get_or_create(name=product_name, defaults={
                "active_substances": list(strength_data.keys())
            })
            medication_strength, created = MedicationStrength.objects.get_or_create(
                medication_name=medication_name, strength=strength_data)
            MedicationNDC.objects.get_or_create(ndc=product["PRODUCTNDC"], defaults={
                "medication_strength": medication_strength,
                "manufacturer": product["LABELERNAME"]
            })
