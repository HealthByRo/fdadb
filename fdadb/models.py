from django.db import models
from django_extensions.db.fields.json import JSONField


class MedicationName(models.Model):
    name = models.CharField(primary_key=True, max_length=255, help_text="Commercial Name (e.g. Viagra)")
    active_substances = JSONField(default=[], blank=True, help_text="List of active substances")

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name

    @property
    def active_substances_list(self):
        if not isinstance(self.active_substances, list):
            return ""

        return ", ".join(self.active_substances)


class MedicationStrength(models.Model):
    STRENGTH_HELP_TEXT = """For example:
    {
        “Sildenafil”: { “strength”: 3, “unit”: “mg/1” }
    }
    """
    medication_name = models.ForeignKey("MedicationName", on_delete=models.CASCADE, related_name="strengths")
    strength = JSONField(default={}, blank=True, help_text=STRENGTH_HELP_TEXT)

    @property
    def name(self):
        return self.medication_name.name

    @property
    def active_substances(self):
        return self.medication_name.active_substances


class MedicationNDC(models.Model):
    medication_strength = models.ForeignKey("MedicationStrength", on_delete=models.CASCADE, related_name="ndcs")
    ndc = models.CharField(max_length=12, unique=True, db_index=True)
    manufacturer = models.CharField(max_length=255, db_index=True)

    def __str__(self):
        return self.ndc

    @property
    def name(self):
        return self.medication_strength.medication_name.name

    @property
    def active_substances(self):
        return self.medication_strength.medication_name.active_substances

    @property
    def strength(self):
        return self.medication_strength.strength
