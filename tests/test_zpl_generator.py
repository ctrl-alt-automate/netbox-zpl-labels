"""Tests for ZPL generator module."""

from unittest.mock import MagicMock

from netbox_zpl_labels.zpl.generator import (
    DANGEROUS_ZPL_COMMANDS,
    LabelData,
    SafeDict,
    ZPLGenerator,
    sanitize_zpl_template,
    validate_zpl_template,
)


class TestZPLGenerator:
    """Tests for ZPLGenerator class."""

    def test_mm_to_dots_300dpi(self):
        """Test millimeter to dots conversion at 300 DPI."""
        generator = ZPLGenerator(dpi=300)

        # 25.4mm = 1 inch = 300 dots at 300 DPI
        assert generator.mm_to_dots(25.4) == 300

        # 1mm ≈ 11.81 dots
        assert generator.mm_to_dots(1) == 11

    def test_mm_to_dots_203dpi(self):
        """Test millimeter to dots conversion at 203 DPI."""
        generator = ZPLGenerator(dpi=203)

        # 25.4mm = 1 inch = 203 dots at 203 DPI
        assert generator.mm_to_dots(25.4) == 203

    def test_sanitize_field_removes_control_chars(self):
        """Test that control characters are removed from field data."""
        generator = ZPLGenerator()

        # Caret and tilde are ZPL special chars
        assert generator.sanitize_field("test^value") == "testvalue"
        assert generator.sanitize_field("test~value") == "testvalue"

        # Control characters should be removed
        assert generator.sanitize_field("test\x00value") == "testvalue"
        assert generator.sanitize_field("test\nvalue") == "testvalue"

    def test_sanitize_field_truncates(self):
        """Test field truncation."""
        generator = ZPLGenerator()

        long_text = "a" * 100
        truncated = generator.sanitize_field(long_text, max_length=20)

        assert len(truncated) == 20
        assert truncated.endswith("...")

    def test_generate_qr_code(self):
        """Test QR code ZPL generation."""
        generator = ZPLGenerator()

        zpl = generator.generate_qr_code(
            url="https://netbox.local/c/1/",
            x=100,
            y=50,
            magnification=5,
        )

        assert "^FO100,50" in zpl
        assert "^BQN,2,5" in zpl
        assert "^FDLA,https://netbox.local/c/1/" in zpl
        assert "^FS" in zpl

    def test_generate_qr_code_clamps_magnification(self):
        """Test that magnification is clamped to valid range."""
        generator = ZPLGenerator()

        # Too low
        zpl = generator.generate_qr_code("http://test", 0, 0, magnification=0)
        assert "^BQN,2,1" in zpl

        # Too high
        zpl = generator.generate_qr_code("http://test", 0, 0, magnification=15)
        assert "^BQN,2,10" in zpl

    def test_generate_text_field(self):
        """Test text field ZPL generation."""
        generator = ZPLGenerator()

        zpl = generator.generate_text_field(
            text="CBL-001",
            x=20,
            y=30,
            font_height=40,
        )

        assert "^FO20,30" in zpl
        assert "^A0N,40,34" in zpl  # width = 40 * 0.87 ≈ 34
        assert "^FDCBL-001^FS" in zpl

    def test_generate_text_field_with_block(self):
        """Test text field with max width and justification."""
        generator = ZPLGenerator()

        zpl = generator.generate_text_field(
            text="Centered Text",
            x=20,
            y=30,
            font_height=28,
            max_width=200,
            justify="C",
        )

        assert "^FB200,1,0,C" in zpl

    def test_generate_box(self):
        """Test graphic box ZPL generation."""
        generator = ZPLGenerator()

        zpl = generator.generate_box(
            x=10,
            y=20,
            width=100,
            height=50,
            thickness=3,
        )

        assert zpl == "^FO10,20^GB100,50,3^FS"

    def test_generate_from_template(self):
        """Test template substitution."""
        generator = ZPLGenerator()

        template = "^XA^FO20,20^FD{cable_id}^FS^XZ"
        data = LabelData(cable_id="CBL-TEST")

        zpl = generator.generate_from_template(template, data)

        assert "^FDCBL-TEST^FS" in zpl

    def test_generate_from_template_with_quantity(self):
        """Test that quantity is added to template."""
        generator = ZPLGenerator()

        template = "^XA^FO20,20^FD{cable_id}^FS^XZ"
        data = LabelData(cable_id="CBL-001")

        zpl = generator.generate_from_template(template, data, quantity=5)

        assert "^PQ5,0,1,Y" in zpl
        assert zpl.endswith("^XZ")

    def test_generate_from_template_replaces_existing_pq(self):
        """Test that existing ^PQ command is replaced."""
        generator = ZPLGenerator()

        template = "^XA^FD{cable_id}^FS^PQ1^XZ"
        data = LabelData(cable_id="CBL-001")

        zpl = generator.generate_from_template(template, data, quantity=10)

        assert "^PQ10,0,1,Y" in zpl
        # The old ^PQ1^ pattern should be replaced (not just substring check)
        # ^PQ10 contains ^PQ1 as substring, so we check for ^PQ1^ specifically
        assert "^PQ1^" not in zpl
        # Should only have one ^PQ command
        assert zpl.count("^PQ") == 1


class TestLabelData:
    """Tests for LabelData class."""

    def test_from_cable_basic(self):
        """Test LabelData creation from Cable mock."""
        cable = MagicMock()
        cable.pk = 42
        cable.label = "CBL-042"
        cable.a_terminations = []
        cable.b_terminations = []
        cable.length = 5.0
        cable.length_unit = "m"
        cable.color = "blue"
        cable.type = "cat6a"
        cable.get_type_display.return_value = "CAT6A"
        cable.description = "Test cable"

        data = LabelData.from_cable(cable, base_url="https://netbox.local")

        assert data.cable_id == "CBL-042"
        assert data.cable_url == "https://netbox.local/dcim/cables/42/"
        assert data.length == "5.0m"
        assert data.color == "blue"
        assert data.cable_type == "CAT6A"
        assert data.description == "Test cable"

    def test_from_cable_without_label(self):
        """Test LabelData when cable has no label."""
        cable = MagicMock()
        cable.pk = 99
        cable.label = None
        cable.a_terminations = []
        cable.b_terminations = []
        cable.length = None
        cable.length_unit = None
        cable.color = None
        cable.type = None
        cable.description = None

        data = LabelData.from_cable(cable)

        assert data.cable_id == "CBL-99"

    def test_from_cable_with_terminations(self):
        """Test LabelData with cable terminations."""
        # Create mock termination A
        term_a = MagicMock()
        term_a.device = MagicMock()
        term_a.device.name = "switch-01"
        term_a.__str__ = MagicMock(return_value="Gi1/0/1")

        # Create mock termination B
        term_b = MagicMock()
        term_b.device = MagicMock()
        term_b.device.name = "server-01"
        term_b.__str__ = MagicMock(return_value="eth0")

        cable = MagicMock()
        cable.pk = 1
        cable.label = "CBL-001"
        cable.a_terminations = [term_a]
        cable.b_terminations = [term_b]
        cable.length = None
        cable.color = None
        cable.type = None
        cable.description = None

        data = LabelData.from_cable(cable)

        assert data.term_a_device == "switch-01"
        assert data.term_a_interface == "Gi1/0/1"
        assert data.term_b_device == "server-01"
        assert data.term_b_interface == "eth0"


class TestSafeDict:
    """Tests for SafeDict class."""

    def test_returns_value_for_existing_key(self):
        """Test that existing keys return their value."""
        d = SafeDict({"foo": "bar"})
        assert d["foo"] == "bar"

    def test_returns_placeholder_for_missing_key(self):
        """Test that missing keys return placeholder."""
        d = SafeDict({"foo": "bar"})
        assert d["missing"] == "{missing}"

    def test_format_string_with_missing_keys(self):
        """Test using SafeDict for format strings."""
        d = SafeDict({"name": "Test"})
        result = "{name}: {value}".format_map(d)
        assert result == "Test: {value}"


class TestZPLInjectionProtection:
    """Tests for ZPL template injection protection."""

    def test_validate_safe_template(self):
        """Test that safe templates pass validation."""
        safe_template = "^XA^FO20,20^ADN,36,20^FD{cable_id}^FS^XZ"
        is_valid, dangerous = validate_zpl_template(safe_template)
        assert is_valid is True
        assert dangerous == []

    def test_validate_detects_image_delete(self):
        """Test that ^ID (image delete) is detected."""
        malicious = "^XA^IDE:LOGO.GRF^FO20,20^FDTest^FS^XZ"
        is_valid, dangerous = validate_zpl_template(malicious)
        assert is_valid is False
        assert "^ID" in dangerous

    def test_validate_detects_download_format(self):
        """Test that ^DF (download format) is detected."""
        malicious = "^XA^DFE:MALICIOUS.ZPL^FO20,20^FDTest^FS^XZ"
        is_valid, dangerous = validate_zpl_template(malicious)
        assert is_valid is False
        assert "^DF" in dangerous

    def test_validate_detects_recall_format(self):
        """Test that ^XF (recall format) is detected."""
        malicious = "^XA^XFE:STORED.ZPL^FS^XZ"
        is_valid, dangerous = validate_zpl_template(malicious)
        assert is_valid is False
        assert "^XF" in dangerous

    def test_validate_detects_network_commands(self):
        """Test that network configuration commands are detected."""
        malicious = "^XA~NC192.168.1.1^FDTest^FS^XZ"
        is_valid, dangerous = validate_zpl_template(malicious)
        assert is_valid is False
        assert "~NC" in dangerous

    def test_validate_case_insensitive(self):
        """Test that detection is case-insensitive."""
        malicious = "^XA^df E:test.zpl^XZ"  # lowercase ^df
        is_valid, dangerous = validate_zpl_template(malicious)
        assert is_valid is False

    def test_validate_detects_multiple_dangerous_commands(self):
        """Test that multiple dangerous commands are all detected."""
        malicious = "^XA^IDE:*.GRF^DFE:BAD.ZPL^~NCBAD^XZ"
        is_valid, dangerous = validate_zpl_template(malicious)
        assert is_valid is False
        assert len(dangerous) == 3

    def test_sanitize_removes_dangerous_commands_with_params(self):
        """Test that sanitize removes dangerous commands AND their parameters."""
        malicious = "^XA^IDE:LOGO.GRF^FO20,20^FDTest^FS^XZ"
        sanitized = sanitize_zpl_template(malicious)
        assert "^ID" not in sanitized
        assert "E:LOGO.GRF" not in sanitized  # Parameters should also be removed
        assert "^FO20,20" in sanitized
        assert "^FDTest^FS" in sanitized

    def test_sanitize_preserves_safe_content(self):
        """Test that sanitize preserves safe ZPL content."""
        safe = "^XA^FO20,20^ADN,36,20^FDHello World^FS^BQN,2,4^FDLA,http://test^FS^XZ"
        sanitized = sanitize_zpl_template(safe)
        assert sanitized == safe

    def test_all_dangerous_commands_listed(self):
        """Test that we have a comprehensive list of dangerous commands."""
        # At minimum, these critical commands should be blocked
        critical_commands = ["^ID", "^DF", "^XF", "~DY", "~NC"]
        for cmd in critical_commands:
            assert cmd in DANGEROUS_ZPL_COMMANDS, f"{cmd} should be in dangerous commands list"
