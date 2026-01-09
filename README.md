# NetBox ZPL Labels Plugin

[![CI](https://github.com/ctrl-alt-automate/netbox-zpl-labels/actions/workflows/ci.yml/badge.svg)](https://github.com/ctrl-alt-automate/netbox-zpl-labels/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![NetBox 4.5+](https://img.shields.io/badge/netbox-4.5+-green.svg)](https://github.com/netbox-community/netbox)

A NetBox plugin for generating and printing ZPL (Zebra Programming Language) labels for cables documented in NetBox. Designed for Zebra thermal transfer printers (ZD421/ZD621 series) with self-laminating cable labels.

## Features

- **Print Cable Labels** directly from NetBox cable detail pages
- **Bulk Printing** - print labels for multiple cables at once
- **Label Preview** - see what your label looks like before printing
- **QR Codes** - include QR codes linking back to NetBox
- **Customizable Templates** - create your own ZPL label templates
- **Printer Management** - manage multiple Zebra printers
- **Print History** - track all print jobs
- **REST API** - integrate with external systems

## Requirements

- **NetBox 4.5+**
- **Python 3.12+**

## Quick Start

### Installation

```bash
pip install git+https://github.com/ctrl-alt-automate/netbox-zpl-labels.git
```

### Enable Plugin

Add to `/opt/netbox/netbox/netbox/configuration.py`:

```python
PLUGINS = [
    'netbox_zpl_labels',
]
```

### Run Migrations

```bash
cd /opt/netbox/netbox
python manage.py migrate
sudo systemctl restart netbox netbox-rq
```

## Configuration

```python
PLUGINS_CONFIG = {
    'netbox_zpl_labels': {
        # Label preview backend options:
        # - 'labelary': Online API (http://labelary.com) - no setup required
        # - 'binarykits': Self-hosted Docker (yipingruan/binarykits-zpl)
        'preview_backend': 'binarykits',

        # URL for BinaryKits preview server (only used when preview_backend = 'binarykits')
        # Docker: docker run -d -p 4040:8080 --restart unless-stopped --name zpl-viewer yipingruan/binarykits-zpl
        'preview_url': 'http://localhost:4040',

        # Uncomment below to use Labelary online API instead:
        # 'preview_backend': 'labelary',
    }
}
```

## Supported Hardware

### Printers
- Zebra ZD421 (203/300 DPI)
- Zebra ZD621 (203/300 DPI)
- Any ZPL-compatible printer via TCP/IP (port 9100)

### Labels
- TE Connectivity Raychem SBP self-laminating labels
- Other ZPL-compatible label stock

## Template Variables

| Variable | Description |
|----------|-------------|
| `{cable_id}` | Cable label or identifier |
| `{cable_url}` | Full URL to cable in NetBox |
| `{term_a_device}` | Device name (A-side) |
| `{term_a_interface}` | Interface name (A-side) |
| `{term_b_device}` | Device name (B-side) |
| `{term_b_interface}` | Interface name (B-side) |
| `{length}` | Cable length with unit |
| `{color}` | Cable color |
| `{type}` | Cable type |
| `{description}` | Cable description |
| `{date}` | Current date (ISO format) |

## Example Template

```zpl
^XA
^FO20,10^ADN,25,12^FD{cable_id}^FS
^FO20,40^ADN,18,10^FDA: {term_a_device}^FS
^FO20,60^ADN,18,10^FD   {term_a_interface}^FS
^FO20,85^ADN,18,10^FDB: {term_b_device}^FS
^FO20,105^ADN,18,10^FD   {term_b_interface}^FS
^XZ
```

## Documentation

See the [Wiki](https://github.com/ctrl-alt-automate/netbox-zpl-labels/wiki) for detailed documentation:

- [Installation](https://github.com/ctrl-alt-automate/netbox-zpl-labels/wiki/Installation)
- [Configuration](https://github.com/ctrl-alt-automate/netbox-zpl-labels/wiki/Configuration)
- [Usage Guide](https://github.com/ctrl-alt-automate/netbox-zpl-labels/wiki/Usage)
- [Label Templates](https://github.com/ctrl-alt-automate/netbox-zpl-labels/wiki/Label-Templates)
- [ZPL Reference](https://github.com/ctrl-alt-automate/netbox-zpl-labels/wiki/ZPL-Reference)

## Development

```bash
# Clone repository
git clone https://github.com/ctrl-alt-automate/netbox-zpl-labels.git
cd netbox-zpl-labels

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
ruff format .
```

## License

Apache License 2.0

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

- [GitHub Issues](https://github.com/ctrl-alt-automate/netbox-zpl-labels/issues)
- [Wiki](https://github.com/ctrl-alt-automate/netbox-zpl-labels/wiki)
