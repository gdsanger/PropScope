from django import forms
from .models import MaidenheadArea
from .services import MaidenheadService


class MaidenheadAreaForm(forms.ModelForm):
    """Form for creating or editing MaidenheadArea entries."""

    class Meta:
        model = MaidenheadArea
        fields = [
            "locator",
            "center_lat",
            "center_lon",
            "primary_country",
            "alternative_countries",
            "continent",
            "is_ambiguous",
            "notes",
        ]
        widgets = {
            "locator": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "z.B. JN68",
                "maxlength": "4",
            }),
            "center_lat": forms.NumberInput(attrs={
                "class": "form-control",
                "readonly": True,
                "step": "0.000001",
            }),
            "center_lon": forms.NumberInput(attrs={
                "class": "form-control",
                "readonly": True,
                "step": "0.000001",
            }),
            "primary_country": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "z.B. Deutschland",
            }),
            "alternative_countries": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Komma-getrennt, z.B. Frankreich, Belgien",
            }),
            "continent": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "z.B. EU, NA, AS",
            }),
            "is_ambiguous": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Zusätzliche Hinweise (optional)",
            }),
        }

    def clean_locator(self):
        """Validate and normalize the locator."""
        locator = self.cleaned_data.get("locator")
        if not locator:
            raise forms.ValidationError("Locator ist erforderlich.")

        # Normalize locator
        service = MaidenheadService()
        normalized = service.normalize_locator(locator)

        # Validate locator format
        if not service.is_valid_locator(normalized):
            raise forms.ValidationError(
                f"Ungültiges Locator-Format: {locator}. "
                "Erwartet: 4 Zeichen, z.B. JN68"
            )

        # Check for duplicate (unless we're updating the same record)
        instance_id = self.instance.pk if self.instance else None
        if MaidenheadArea.objects.filter(locator=normalized).exclude(pk=instance_id).exists():
            raise forms.ValidationError(
                f"Locator {normalized} existiert bereits. "
                "Bitte bearbeiten Sie den vorhandenen Eintrag."
            )

        return normalized

    def clean(self):
        """Additional validation."""
        cleaned_data = super().clean()
        primary_country = cleaned_data.get("primary_country")
        continent = cleaned_data.get("continent")

        if not primary_country:
            raise forms.ValidationError("Primäres Land ist erforderlich.")

        if not continent:
            raise forms.ValidationError("Kontinent ist erforderlich.")

        return cleaned_data
