from django.contrib import admin

from fdadb.models import MedicationName


class MedicationNameAdmin(admin.ModelAdmin):
    list_display = ["name", "active_substances_list"]
    sortable_by = ["name"]
    search_fields = ["name", "active_substances"]

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        if obj:
            return False

        # allow listing medications in admin
        return True


admin.site.register(MedicationName, MedicationNameAdmin)
