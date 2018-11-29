import io
import os.path
import zipfile
from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from fdadb.management.commands import fetch_ndc_database
from fdadb.models import MedicationName, MedicationNDC, MedicationStrength

THIS_FILE_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_PRODUCT_FILE = os.path.join(THIS_FILE_DIR, "test_data", "product.txt")


def as_zip_file(names_and_contents):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
        for file_name, data in names_and_contents:
            zip_file.writestr(file_name, data)
    return zip_buffer.getvalue()


def fake_database_file():
    with open(TEST_PRODUCT_FILE, "rb") as f:
        return as_zip_file([("product.txt", f.read())])


class FetchNdcDatabaseTestCase(TestCase):
    @mock.patch.object(fetch_ndc_database.Command, "fetch_database_file")
    def test_command(self, fetch_database_file):
        fetch_database_file.return_value = fake_database_file()

        for model in (MedicationName, MedicationNDC, MedicationStrength):
            self.assertEqual(model.objects.count(), 0)

        call_command("fetch_ndc_database")
        meds = {o.name: o for o in MedicationName.objects.all()}
        self.assertEqual(sorted(meds.keys()), ["Drug A Suffix A", "Drug B Suffix B"])

        med_a = meds["Drug A Suffix A"]
        self.assertEqual(sorted(med_a.active_substances), ["Substance A"])
        med_b = meds["Drug B Suffix B"]
        self.assertEqual(sorted(med_b.active_substances), ["Substance B-1", "Substance B-2"])

        def strength_and_ndc_entries(medication_ndc):
            return (
                medication_ndc.medication_strength.medication_name,
                medication_ndc.medication_strength.strength,
                (medication_ndc.ndc, medication_ndc.manufacturer),
            )

        self.assertEqual(
            [strength_and_ndc_entries(o) for o in MedicationNDC.objects.order_by("pk")],
            [
                (
                    med_a,
                    {"Substance A": {"strength": "10", "unit": "mg/1"}},
                    ("0001-0", "Labeler A"),
                ),
                (
                    med_a,
                    {"Substance A": {"strength": "40", "unit": "mg/1"}},
                    ("0001-1", "Labeler A"),
                ),
                (
                    med_b,
                    {
                        "Substance B-1": {"strength": "10", "unit": "mg/1"},
                        "Substance B-2": {"strength": "11", "unit": "mg/mL"},
                    },
                    ("0001-2", "Labeler B"),
                ),
                (
                    med_b,
                    {
                        "Substance B-1": {"strength": "20", "unit": "mg/1"},
                        "Substance B-2": {"strength": "21", "unit": "mg/mL"},
                    },
                    ("0001-3", "Labeler B"),
                ),
            ],
        )
