from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from fdadb.models import MedicationName, MedicationNDC, MedicationStrength


class APITests(APITestCase):
    def setUp(self):
        for name in ("DrugName", "OtherDrugName", "DruuuugName", "NamedDrug"):
            medication_name = MedicationName.objects.create(
                name=name, active_substances=[name + " Substance 1", name + " Substance 2"]
            )

            for strength in (1, 2, 3):
                medication_strength = MedicationStrength.objects.create(
                    medication_name=medication_name,
                    strength={
                        name + " Substance 1": {"strength": strength, "unit": "mg/l"},
                        name + " Substance 2": {"strength": strength + 5, "unit": "mg/l"},
                    },
                )

                for manufacturer in ("M1", "M2"):
                    MedicationNDC.objects.create(
                        medication_strength=medication_strength,
                        ndc=name[:5] + str(strength) + manufacturer,
                        manufacturer=manufacturer,
                    )

    def test_names_api(self):
        url = reverse("fdadb-medications-names")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 4)
        self.assertEqual(response.data["results"][0]["name"], "DrugName")
        self.assertEqual(
            response.data["results"][0]["active_substances"], ["DrugName Substance 1", "DrugName Substance 2"]
        )

        response = self.client.get(url + "?q=Druuu")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "DruuuugName")
        self.assertEqual(
            response.data["results"][0]["active_substances"], ["DruuuugName Substance 1", "DruuuugName Substance 2"]
        )

    def test_strengths_api(self):
        url = reverse("fdadb-medications-strengths", kwargs={"medication_name": "NamedDrug"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(response.data["results"][0]["name"], "NamedDrug")
        self.assertEqual(
            response.data["results"][0]["active_substances"], ["NamedDrug Substance 1", "NamedDrug Substance 2"]
        )
        self.assertEqual(
            response.data["results"][0]["strength"],
            {
                "NamedDrug Substance 1": {"strength": 1, "unit": "mg/l"},
                "NamedDrug Substance 2": {"strength": 6, "unit": "mg/l"},
            },
        )

        response = self.client.get(url + "?q=3")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "NamedDrug")
        self.assertEqual(
            response.data["results"][0]["active_substances"], ["NamedDrug Substance 1", "NamedDrug Substance 2"]
        )
        self.assertEqual(
            response.data["results"][0]["strength"],
            {
                "NamedDrug Substance 1": {"strength": 3, "unit": "mg/l"},
                "NamedDrug Substance 2": {"strength": 8, "unit": "mg/l"},
            },
        )

    def test_ndcs_api(self):
        strength = MedicationStrength.objects.filter(medication_name__name="OtherDrugName").first()
        url = reverse("fdadb-medications-ndcs", kwargs={"medication_name": "OtherDrugName", "strength_id": strength.pk})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["name"], "OtherDrugName")
        self.assertEqual(
            response.data["results"][0]["active_substances"], ["OtherDrugName Substance 1", "OtherDrugName Substance 2"]
        )
        self.assertEqual(
            response.data["results"][0]["strength"],
            {
                "OtherDrugName Substance 1": {"strength": 1, "unit": "mg/l"},
                "OtherDrugName Substance 2": {"strength": 6, "unit": "mg/l"},
            },
        )
        self.assertEqual(response.data["results"][0]["manufacturer"], "M1")
        self.assertEqual(response.data["results"][0]["ndc"], "Other1M1")

        strength = MedicationStrength.objects.filter(medication_name__name="OtherDrugName").first()
        url = reverse("fdadb-medications-ndcs", kwargs={"medication_name": "OtherDrugName", "strength_id": strength.pk})

        response = self.client.get(url + "?q=m2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "OtherDrugName")
        self.assertEqual(
            response.data["results"][0]["active_substances"], ["OtherDrugName Substance 1", "OtherDrugName Substance 2"]
        )
        self.assertEqual(
            response.data["results"][0]["strength"],
            {
                "OtherDrugName Substance 1": {"strength": 1, "unit": "mg/l"},
                "OtherDrugName Substance 2": {"strength": 6, "unit": "mg/l"},
            },
        )
        self.assertEqual(response.data["results"][0]["manufacturer"], "M2")
        self.assertEqual(response.data["results"][0]["ndc"], "Other1M2")
