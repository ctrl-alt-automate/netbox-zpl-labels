"""Tests for printer communication module."""

from unittest.mock import MagicMock, patch

from netbox_zpl_labels.zpl.printer import (
    PrintResult,
    ZPLPrinterClient,
    check_printer_connection,
    send_to_printer,
)


class TestPrintResult:
    """Tests for PrintResult dataclass."""

    def test_success_result(self):
        """Test successful print result."""
        result = PrintResult(success=True, bytes_sent=256)
        assert result.success is True
        assert result.error is None
        assert result.bytes_sent == 256

    def test_failure_result(self):
        """Test failed print result."""
        result = PrintResult(success=False, error="Connection refused")
        assert result.success is False
        assert result.error == "Connection refused"
        assert result.bytes_sent == 0


class TestZPLPrinterClient:
    """Tests for ZPLPrinterClient class."""

    def test_init_defaults(self):
        """Test client initialization with defaults."""
        client = ZPLPrinterClient(host="192.168.1.100")
        assert client.host == "192.168.1.100"
        assert client.port == 9100
        assert client.timeout == 5.0

    def test_init_custom(self):
        """Test client initialization with custom values."""
        client = ZPLPrinterClient(
            host="printer.local",
            port=9101,
            timeout=10.0,
        )
        assert client.host == "printer.local"
        assert client.port == 9101
        assert client.timeout == 10.0

    @patch("socket.socket")
    def test_test_connection_success(self, mock_socket_class):
        """Test successful connection test."""
        mock_socket = MagicMock()
        mock_socket_class.return_value.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket_class.return_value.__exit__ = MagicMock(return_value=False)

        client = ZPLPrinterClient(host="192.168.1.100")
        result = client.test_connection()

        assert result.success is True
        mock_socket.connect.assert_called_once_with(("192.168.1.100", 9100))

    @patch("socket.socket")
    def test_test_connection_timeout(self, mock_socket_class):
        """Test connection timeout."""
        mock_socket = MagicMock()
        mock_socket.connect.side_effect = TimeoutError()
        mock_socket_class.return_value.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket_class.return_value.__exit__ = MagicMock(return_value=False)

        client = ZPLPrinterClient(host="192.168.1.100", timeout=2.0)
        result = client.test_connection()

        assert result.success is False
        assert "timeout" in result.error.lower()

    @patch("socket.socket")
    def test_test_connection_refused(self, mock_socket_class):
        """Test connection refused."""
        mock_socket = MagicMock()
        mock_socket.connect.side_effect = OSError("Connection refused")
        mock_socket_class.return_value.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket_class.return_value.__exit__ = MagicMock(return_value=False)

        client = ZPLPrinterClient(host="192.168.1.100")
        result = client.test_connection()

        assert result.success is False
        assert "Connection" in result.error

    @patch("socket.socket")
    def test_send_zpl_success(self, mock_socket_class):
        """Test successful ZPL send."""
        mock_socket = MagicMock()
        mock_socket.send.return_value = 42
        mock_socket_class.return_value.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket_class.return_value.__exit__ = MagicMock(return_value=False)

        client = ZPLPrinterClient(host="192.168.1.100")
        result = client.send_zpl("^XA^FO20,20^FDTEST^FS^XZ")

        assert result.success is True
        assert result.bytes_sent == 42
        mock_socket.send.assert_called_once()

    @patch("socket.socket")
    def test_send_zpl_empty_content(self, mock_socket_class):
        """Test sending empty ZPL."""
        client = ZPLPrinterClient(host="192.168.1.100")
        result = client.send_zpl("")

        assert result.success is False
        assert "Empty" in result.error

    @patch("socket.socket")
    def test_send_zpl_socket_error(self, mock_socket_class):
        """Test socket error during send."""
        mock_socket = MagicMock()
        mock_socket.send.side_effect = OSError("Broken pipe")
        mock_socket_class.return_value.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket_class.return_value.__exit__ = MagicMock(return_value=False)

        client = ZPLPrinterClient(host="192.168.1.100")
        result = client.send_zpl("^XA^XZ")

        assert result.success is False
        assert "error" in result.error.lower()

    @patch("socket.socket")
    def test_send_zpl_batch(self, mock_socket_class):
        """Test batch ZPL send."""
        mock_socket = MagicMock()
        mock_socket.send.return_value = 20
        mock_socket_class.return_value.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket_class.return_value.__exit__ = MagicMock(return_value=False)

        client = ZPLPrinterClient(host="192.168.1.100")
        results = client.send_zpl_batch(
            [
                "^XA^FDLABEL1^FS^XZ",
                "^XA^FDLABEL2^FS^XZ",
                "^XA^FDLABEL3^FS^XZ",
            ]
        )

        assert len(results) == 3
        assert all(r.success for r in results)
        assert mock_socket.send.call_count == 3

    def test_send_zpl_batch_empty_list(self):
        """Test batch send with empty list."""
        client = ZPLPrinterClient(host="192.168.1.100")
        results = client.send_zpl_batch([])
        assert results == []


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    @patch("netbox_zpl_labels.zpl.printer.ZPLPrinterClient")
    def test_send_to_printer(self, mock_client_class):
        """Test send_to_printer convenience function."""
        mock_client = MagicMock()
        mock_client.send_zpl.return_value = PrintResult(success=True, bytes_sent=100)
        mock_client_class.return_value = mock_client

        success, error = send_to_printer(
            host="192.168.1.100",
            port=9100,
            zpl_content="^XA^XZ",
        )

        assert success is True
        assert error is None
        mock_client_class.assert_called_once_with(
            host="192.168.1.100",
            port=9100,
            timeout=5.0,
        )

    @patch("netbox_zpl_labels.zpl.printer.ZPLPrinterClient")
    def test_check_printer_connection(self, mock_client_class):
        """Test check_printer_connection convenience function."""
        mock_client = MagicMock()
        mock_client.test_connection.return_value = PrintResult(success=True)
        mock_client_class.return_value = mock_client

        success, error = check_printer_connection(
            host="printer.local",
            port=9100,
        )

        assert success is True
        assert error is None
