"""Tests for ZPL templates module."""

from netbox_zpl_labels.zpl.templates import (
    DEFAULT_TEMPLATES,
    TEMPLATE_SBP100143_MINIMAL,
    TEMPLATE_SBP100225_STANDARD,
    TEMPLATE_SBP100375_FULL,
    get_default_template,
    get_template_by_name,
)


class TestDefaultTemplates:
    """Tests for default template definitions."""

    def test_all_templates_have_required_fields(self):
        """Test that all templates have required fields."""
        for template in DEFAULT_TEMPLATES:
            assert template.name
            assert template.description
            assert template.label_size
            assert template.width_mm > 0
            assert template.height_mm > 0
            assert "^XA" in template.zpl_template
            assert "^XZ" in template.zpl_template

    def test_sbp100375_full_template(self):
        """Test the full-featured large label template."""
        template = TEMPLATE_SBP100375_FULL

        assert template.label_size == "sbp100375"
        assert template.width_mm == 25.4
        assert template.include_qr is True
        assert template.qr_magnification == 5

        # Check for expected placeholders
        assert "{cable_id}" in template.zpl_template
        assert "{cable_url}" in template.zpl_template
        assert "{term_a_device}" in template.zpl_template
        assert "{term_b_device}" in template.zpl_template

    def test_sbp100225_standard_template(self):
        """Test the medium label template."""
        template = TEMPLATE_SBP100225_STANDARD

        assert template.label_size == "sbp100225"
        assert template.width_mm == 19.1
        assert template.qr_magnification == 4

    def test_sbp100143_minimal_template(self):
        """Test the small minimal template."""
        template = TEMPLATE_SBP100143_MINIMAL

        assert template.label_size == "sbp100143"
        assert template.width_mm == 12.7
        assert template.qr_magnification == 3

    def test_templates_have_valid_zpl_structure(self):
        """Test that templates have valid ZPL command structure."""
        for template in DEFAULT_TEMPLATES:
            zpl = template.zpl_template

            # Must start with ^XA and end with ^XZ
            assert zpl.strip().startswith("^XA")
            assert zpl.strip().endswith("^XZ")

            # Should have at least one field
            assert "^FO" in zpl or "^FT" in zpl


class TestGetDefaultTemplate:
    """Tests for get_default_template function."""

    def test_get_sbp100375(self):
        """Test getting default template for SBP100375."""
        template = get_default_template("sbp100375")
        assert template is not None
        assert template.label_size == "sbp100375"

    def test_get_sbp100225(self):
        """Test getting default template for SBP100225."""
        template = get_default_template("sbp100225")
        assert template is not None
        assert template.label_size == "sbp100225"

    def test_get_sbp100143(self):
        """Test getting default template for SBP100143."""
        template = get_default_template("sbp100143")
        assert template is not None
        assert template.label_size == "sbp100143"

    def test_get_unknown_size_returns_none(self):
        """Test that unknown size returns None."""
        template = get_default_template("unknown_size")
        assert template is None


class TestGetTemplateByName:
    """Tests for get_template_by_name function."""

    def test_get_by_exact_name(self):
        """Test getting template by exact name."""
        template = get_template_by_name("SBP100375 Full")
        assert template is not None
        assert template.name == "SBP100375 Full"

    def test_get_compact_template(self):
        """Test getting compact template."""
        template = get_template_by_name("SBP100375 Compact")
        assert template is not None
        assert "Compact" in template.name

    def test_get_unknown_name_returns_none(self):
        """Test that unknown name returns None."""
        template = get_template_by_name("Non-existent Template")
        assert template is None


class TestTemplateZPLContent:
    """Tests for template ZPL content specifics."""

    def test_templates_set_print_width(self):
        """Test that templates set appropriate print width."""
        for template in DEFAULT_TEMPLATES:
            # Should have ^PW command for print width
            assert "^PW" in template.zpl_template

    def test_templates_have_print_quantity(self):
        """Test that templates have print quantity command."""
        for template in DEFAULT_TEMPLATES:
            # Should have ^PQ command (may be ^PQ1)
            assert "^PQ" in template.zpl_template

    def test_qr_templates_have_bq_command(self):
        """Test that templates with QR codes have ^BQ command."""
        for template in DEFAULT_TEMPLATES:
            if template.include_qr:
                assert "^BQ" in template.zpl_template
                assert "{cable_url}" in template.zpl_template
