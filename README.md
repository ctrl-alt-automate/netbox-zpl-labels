# NetBox ZPL Labels Plugin

A NetBox plugin for generating and printing ZPL (Zebra Programming Language) labels for cables documented in NetBox. The plugin targets Zebra thermal transfer printers (ZD421/ZD621 series) with self-laminating cable labels.

## Features

- **ZPL Label Generation**: Generate ZPL code from NetBox Cable objects
- **QR Codes**: Include QR codes linking directly to cable detail pages in NetBox
- **Direct Printing**: Send labels directly to Zebra printers via TCP/IP (port 9100)
- **Label Preview**: Preview labels before printing using the Labelary API
- **Batch Printing**: Print labels for multiple cables at once
- **Customizable Templates**: Create and manage label templates for different label sizes
- **Print History**: Track all print operations for auditing

## Supported Hardware

### Printers
- Zebra ZD421 (203/300 DPI)
- Zebra ZD621 (203/300 DPI)
- Any Zebra printer supporting ZPL II via TCP/IP

### Labels
- TE Connectivity Raychem SBP self-laminating labels:
  - SBP050100 (8.5mm × 25.4mm)
  - SBP100143 (12.7mm × 36.5mm)
  - SBP100225 (19.1mm × 57.2mm)
  - SBP100375 (25.4mm × 95.3mm)
  - SBP200375 (25.4mm × 95.3mm wide)

## Requirements

- NetBox 4.0+
- Python 3.10+

### Optional Dependencies
- `requests` - For label preview functionality (Labelary API)

## Installation

### From PyPI (when published)
```bash
pip install netbox-zpl-labels
```

### From Source
```bash
git clone https://github.com/youruser/netbox-zpl-labels.git
cd netbox-zpl-labels
pip install -e .
```

### Configuration

Add the plugin to your NetBox `configuration.py`:

```python
PLUGINS = [
    'netbox_zpl_labels',
]

PLUGINS_CONFIG = {
    'netbox_zpl_labels': {
        'default_dpi': 300,
        'labelary_enabled': True,
        'socket_timeout': 5,
    },
}
```

Run database migrations:
```bash
cd /opt/netbox/netbox
python manage.py migrate netbox_zpl_labels
```

Restart NetBox:
```bash
sudo systemctl restart netbox netbox-rq
```

## Usage

### Configure Printers

1. Navigate to **Plugins > ZPL Labels > Printers**
2. Click **Add** to create a new printer
3. Enter the printer's IP address and port (default: 9100)
4. Test the connection

### Create Label Templates

1. Navigate to **Plugins > ZPL Labels > Label Templates**
2. Click **Add** to create a new template
3. Select the label size and enter the ZPL template code
4. Use placeholders like `{cable_id}`, `{cable_url}`, `{term_a_device}`, etc.
5. Set as default template if desired

### Print Labels

#### Single Cable
1. Navigate to any Cable detail page
2. Click the **Print Label** tab
3. Select printer and template
4. Click **Print**

#### Multiple Cables
1. Navigate to **DCIM > Cables**
2. Select the cables you want to print
3. Click **Print Labels**
4. Select printer and template
5. Click **Print All Labels**

### REST API

The plugin provides a REST API for integration with external systems:

```bash
# Generate ZPL code
POST /api/plugins/zpl-labels/labels/generate/
{
    "cable_ids": [1, 2, 3],
    "template_id": 1
}

# Print labels
POST /api/plugins/zpl-labels/labels/print/
{
    "cable_ids": [1, 2, 3],
    "printer_id": 1,
    "template_id": 1,
    "copies": 2
}

# Get label preview
GET /api/plugins/zpl-labels/labels/preview/?cable_id=1&template_id=1
```

## Template Variables

The following variables are available in label templates:

| Variable | Description |
|----------|-------------|
| `{cable_id}` | Cable label or identifier |
| `{cable_url}` | Full URL to cable in NetBox |
| `{term_a_device}` | Device name (A-side termination) |
| `{term_a_interface}` | Interface name (A-side termination) |
| `{term_b_device}` | Device name (B-side termination) |
| `{term_b_interface}` | Interface name (B-side termination) |
| `{length}` | Cable length with unit |
| `{color}` | Cable color |
| `{type}` | Cable type |
| `{description}` | Cable description |
| `{date}` | Current date (ISO format) |

## Example Template

```zpl
^XA
^PW300
^LL450

^FO24,24^A0N,42,36^FD{cable_id}^FS

^FO180,20^BQN,2,5^FDLA,{cable_url}^FS

^FO24,75^A0N,22,18^FDFrom: {term_a_device}^FS
^FO24,100^A0N,20,16^FD  {term_a_interface}^FS

^FO24,130^A0N,22,18^FDTo: {term_b_device}^FS
^FO24,155^A0N,20,16^FD  {term_b_interface}^FS

^FO24,185^GB252,2,2^FS

^FO24,195^A0N,20,16^FD{type} {length}^FS

^PQ1,0,1,Y
^XZ
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/youruser/netbox-zpl-labels.git
cd netbox-zpl-labels

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
ruff format .

# Type checking
mypy netbox_zpl_labels
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=netbox_zpl_labels tests/

# Run specific test file
pytest tests/test_zpl_generator.py
```

## License

Apache License 2.0

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

- [GitHub Issues](https://github.com/youruser/netbox-zpl-labels/issues)
- [NetBox Community](https://github.com/netbox-community/netbox/discussions)
