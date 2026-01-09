"""TCP/IP printer communication for Zebra ZPL printers.

This module handles direct socket communication with Zebra thermal
printers via TCP port 9100.
"""

from __future__ import annotations

import logging
import socket
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class PrintResult:
    """Result of a print operation.

    Attributes:
        success: Whether the print was successful
        error: Error message if failed, None otherwise
        bytes_sent: Number of bytes sent to printer
    """

    success: bool
    error: str | None = None
    bytes_sent: int = 0


class ZPLPrinterClient:
    """Client for communicating with Zebra ZPL printers.

    Handles TCP/IP socket communication to send ZPL code
    directly to the printer.
    """

    DEFAULT_PORT = 9100
    DEFAULT_TIMEOUT = 5.0

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """Initialize the printer client.

        Args:
            host: Printer IP address or hostname
            port: TCP port (default: 9100)
            timeout: Socket timeout in seconds
        """
        self.host = host
        self.port = port
        self.timeout = timeout

    def test_connection(self) -> PrintResult:
        """Test connectivity to the printer.

        Attempts to establish a TCP connection to verify
        the printer is reachable.

        Returns:
            PrintResult indicating success or failure
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                sock.connect((self.host, self.port))
                return PrintResult(success=True)
        except TimeoutError:
            return PrintResult(
                success=False,
                error=f"Connection timeout after {self.timeout}s",
            )
        except OSError as e:
            return PrintResult(
                success=False,
                error=f"Connection failed: {e}",
            )

    def send_zpl(self, zpl_content: str) -> PrintResult:
        """Send ZPL code to the printer.

        Args:
            zpl_content: ZPL code string to send

        Returns:
            PrintResult indicating success or failure
        """
        if not zpl_content:
            return PrintResult(success=False, error="Empty ZPL content")

        # Encode to bytes
        try:
            data = zpl_content.encode("utf-8")
        except UnicodeEncodeError as e:
            return PrintResult(success=False, error=f"Encoding error: {e}")

        # Send to printer
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                sock.connect((self.host, self.port))

                bytes_sent = sock.send(data)

                logger.info(
                    "Sent %d bytes to printer %s:%d",
                    bytes_sent,
                    self.host,
                    self.port,
                )

                return PrintResult(success=True, bytes_sent=bytes_sent)

        except TimeoutError:
            error = f"Connection timeout after {self.timeout}s"
            logger.error("Printer %s:%d - %s", self.host, self.port, error)
            return PrintResult(success=False, error=error)

        except OSError as e:
            error = f"Socket error: {e}"
            logger.error("Printer %s:%d - %s", self.host, self.port, error)
            return PrintResult(success=False, error=error)

    def send_zpl_batch(self, zpl_contents: list[str]) -> list[PrintResult]:
        """Send multiple ZPL jobs to the printer.

        Opens a single connection and sends all ZPL content sequentially.
        More efficient than multiple send_zpl calls for batch printing.

        Args:
            zpl_contents: List of ZPL code strings

        Returns:
            List of PrintResult for each job
        """
        if not zpl_contents:
            return []

        results = []

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                sock.connect((self.host, self.port))

                for zpl in zpl_contents:
                    try:
                        data = zpl.encode("utf-8")
                        bytes_sent = sock.send(data)
                        results.append(PrintResult(success=True, bytes_sent=bytes_sent))
                    except (OSError, UnicodeEncodeError) as e:
                        results.append(PrintResult(success=False, error=str(e)))

        except TimeoutError:
            error = f"Connection timeout after {self.timeout}s"
            # Mark remaining jobs as failed
            for _ in range(len(zpl_contents) - len(results)):
                results.append(PrintResult(success=False, error=error))

        except OSError as e:
            error = f"Socket error: {e}"
            for _ in range(len(zpl_contents) - len(results)):
                results.append(PrintResult(success=False, error=error))

        return results

    def get_printer_status(self) -> dict[str, str] | None:
        """Query printer status using Host Status Return command.

        Sends ~HS command and parses the response.

        Returns:
            Dictionary with status info or None if failed
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                sock.connect((self.host, self.port))

                # Send Host Status command
                sock.send(b"~HS")

                # Try to receive response
                sock.settimeout(2.0)
                response = sock.recv(4096)

                if response:
                    return self._parse_status_response(response.decode("utf-8"))

        except OSError as e:
            logger.debug("Status query failed: %s", e)

        return None

    def _parse_status_response(self, response: str) -> dict[str, str]:
        """Parse printer status response.

        Args:
            response: Raw response string from printer

        Returns:
            Dictionary with parsed status fields
        """
        # Basic parsing - full implementation depends on printer model
        status = {
            "raw_response": response,
            "online": "online" if response else "unknown",
        }

        # Parse common status indicators
        if "PAPER OUT" in response.upper():
            status["paper"] = "out"
        elif "PAPER" in response.upper():
            status["paper"] = "ok"

        if "RIBBON OUT" in response.upper():
            status["ribbon"] = "out"
        elif "RIBBON" in response.upper():
            status["ribbon"] = "ok"

        return status


def send_to_printer(
    host: str,
    port: int,
    zpl_content: str,
    timeout: float = 5.0,
) -> tuple[bool, str | None]:
    """Send ZPL content to a printer.

    Convenience function for single print operations.

    Args:
        host: Printer IP address or hostname
        port: TCP port
        zpl_content: ZPL code to send
        timeout: Socket timeout in seconds

    Returns:
        Tuple of (success: bool, error: str | None)
    """
    client = ZPLPrinterClient(host=host, port=port, timeout=timeout)
    result = client.send_zpl(zpl_content)
    return result.success, result.error


def check_printer_connection(
    host: str,
    port: int = 9100,
    timeout: float = 5.0,
) -> tuple[bool, str | None]:
    """Check connection to a printer.

    Args:
        host: Printer IP address or hostname
        port: TCP port
        timeout: Socket timeout in seconds

    Returns:
        Tuple of (success: bool, error: str | None)
    """
    client = ZPLPrinterClient(host=host, port=port, timeout=timeout)
    result = client.test_connection()
    return result.success, result.error
