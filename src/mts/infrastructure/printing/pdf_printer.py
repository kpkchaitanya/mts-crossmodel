"""Send an exported PDF to a local Windows printer.

Backends are external viewers driven by explicit argument lists (never a shell string). Nothing here
knows about worksheets, grades, or copy policy; the caller supplies the bytes and the copy count.
"""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any
import re
import subprocess
import tempfile

SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")
# SumatraPDF -print-settings tokens; simplex is the safe default for a printer without a duplex unit.
DUPLEX_SETTINGS = {"simplex": "simplex", "duplex_long": "duplexlong", "duplex_short": "duplexshort"}


class PdfPrinterError(RuntimeError):
    """Raised when a PDF could not be spooled to the printer."""


class _BasePdfPrinter:
    backend = "base"

    def __init__(self, executable: str | Path, *, printer_name: str, duplex: str = "simplex", spool_dir: str | Path | None = None) -> None:
        if not printer_name:
            raise PdfPrinterError("printer_name is required.")
        if duplex not in DUPLEX_SETTINGS:
            raise PdfPrinterError(f"duplex must be one of {', '.join(DUPLEX_SETTINGS)}.")
        self.executable = Path(executable)
        self.printer_name = printer_name
        self.duplex = duplex
        self.spool_dir = Path(spool_dir) if spool_dir else Path(tempfile.gettempdir()) / "mts-print"

    def _spool_file(self, content: bytes, name: str) -> Path:
        if not content:
            raise PdfPrinterError(f"No PDF content to print for '{name}'.")
        if not self.executable.is_file():
            raise PdfPrinterError(f"Print backend executable not found: {self.executable}")
        self.spool_dir.mkdir(parents=True, exist_ok=True)
        path = self.spool_dir / f"{SAFE_NAME.sub('_', name).strip('_') or 'document'}.pdf"
        path.write_bytes(content)
        return path

    def _run(self, command: list[str], path: Path) -> None:
        completed = subprocess.run(command, capture_output=True, text=True)  # noqa: S603  (fixed argv, no shell)
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            raise PdfPrinterError(f"{self.backend} failed to print {path.name} (exit {completed.returncode}): {detail}")


class SumatraPdfPrinter(_BasePdfPrinter):
    """Silent printing with exact copy and duplex control."""

    backend = "sumatra"

    def print_pdf(self, content: bytes, *, name: str, copies: int) -> dict[str, Any]:
        if copies < 1:
            raise PdfPrinterError(f"copies must be at least 1 for '{name}'.")
        path = self._spool_file(content, name)
        command = [
            str(self.executable),
            "-print-to", self.printer_name,
            "-print-settings", f"{copies}x,{DUPLEX_SETTINGS[self.duplex]}",
            "-silent", "-exit-when-done",
            str(path),
        ]
        self._run(command, path)
        return {"backend": self.backend, "printer": self.printer_name, "copies": copies, "duplex": self.duplex, "file": str(path)}


class AcrobatPdfPrinter(_BasePdfPrinter):
    """Fallback for machines without SumatraPDF: one Acrobat invocation per copy, printer defaults for duplex."""

    backend = "acrobat"

    def print_pdf(self, content: bytes, *, name: str, copies: int) -> dict[str, Any]:
        if copies < 1:
            raise PdfPrinterError(f"copies must be at least 1 for '{name}'.")
        path = self._spool_file(content, name)
        for _ in range(copies):
            self._run([str(self.executable), "/n", "/t", str(path), self.printer_name], path)
        return {"backend": self.backend, "printer": self.printer_name, "copies": copies, "duplex": "printer_default", "file": str(path)}


BACKENDS = {"sumatra": SumatraPdfPrinter, "acrobat": AcrobatPdfPrinter}


def build_printer(
    settings: Mapping[str, Any],
    *,
    repository_root: str | Path,
    backend: str | None = None,
    printer_name: str | None = None,
) -> _BasePdfPrinter:
    """Construct the configured backend; an unknown or unconfigured backend fails closed."""
    name = backend or settings.get("backend")
    if name not in BACKENDS:
        raise PdfPrinterError(f"backend must be one of {', '.join(BACKENDS)}.")
    backend_settings = (settings.get("backends") or {}).get(name) or {}
    executable = backend_settings.get("executable")
    if not executable:
        raise PdfPrinterError(f"publishing.printing.backends.{name}.executable is not configured.")
    path = Path(executable)
    if not path.is_absolute():
        path = Path(repository_root) / path
    spool_dir = settings.get("spool_dir")
    if spool_dir and not Path(spool_dir).is_absolute():
        spool_dir = Path(repository_root) / spool_dir
    return BACKENDS[name](
        path,
        printer_name=printer_name or settings.get("printer_name", ""),
        duplex=settings.get("duplex", "simplex"),
        spool_dir=spool_dir,
    )


__all__ = ["AcrobatPdfPrinter", "PdfPrinterError", "SumatraPdfPrinter", "build_printer", "DUPLEX_SETTINGS"]
