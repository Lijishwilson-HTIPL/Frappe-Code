"""Virus/malware scanning for uploaded files.

Synchronous Frappe port of the MFT malware scanner
(Malwarescannerservice.py / Malwarescanintegration.py).

Every File inserted on the site is scanned before it is saved.
Engines, in priority order:
  1. ClamAV daemon via pyclamd (production engine, if installed/reachable)
  2. Pattern-match fallback (pure Python, always available)

Policy (fail-closed):
  CLEAN      -> allowed
  SKIPPED    -> allowed (file larger than scan_max_file_size)
  INFECTED   -> blocked + quarantined
  SUSPICIOUS -> blocked + quarantined (virus_scan_block_suspicious=0 to allow)
  ERROR      -> blocked (virus_scan_block_on_error=0 to allow)

Site config keys (site_config.json), all optional:
  virus_scan_enabled           default 1
  virus_scan_max_file_size     default 104857600 (100 MB)
  virus_scan_block_suspicious  default 1
  virus_scan_block_on_error    default 1
  virus_scan_block_executables default 1
  clamav_host / clamav_port / clamav_socket
"""

import hashlib
import json
import os
import shutil
import time

import frappe
from frappe import _
from frappe.utils import now_datetime

CLEAN = "CLEAN"
INFECTED = "INFECTED"
SUSPICIOUS = "SUSPICIOUS"
ERROR = "ERROR"
SKIPPED = "SKIPPED"

EICAR_SIGNATURE = (
	b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
)

EXECUTABLE_SIGNATURES = {
	b"MZ": "PE (Windows) executable",
	b"\x7fELF": "ELF (Linux) executable",
}


def _conf(key, default):
	value = frappe.conf.get(key)
	return default if value is None else value


def _logger():
	import logging

	log = frappe.logger("virus_scan", allow_site=True)
	log.setLevel(logging.INFO)
	return log


def scan_file_before_insert(doc, method=None):
	"""doc_events hook: File.before_insert. Blocks infected uploads."""
	if not int(_conf("virus_scan_enabled", 1)):
		return
	if doc.is_folder or (doc.file_url or "").startswith("http"):
		return

	try:
		content = _get_file_content(doc)
	except _ContentUnreadable as e:
		# Fail closed: if the bytes cannot be read they cannot be certified
		# clean. Honor the block-on-error policy rather than saving unscanned.
		_logger().error(f"virus_scan could not read content of {doc.file_name}: {e}")
		if int(_conf("virus_scan_block_on_error", 1)):
			frappe.throw(
				_("File {0} could not be read for virus scanning and was blocked for safety.").format(
					frappe.bold(doc.file_name)
				),
				title=_("Virus Scan Failed"),
			)
		return

	# Genuinely empty file (0 bytes) — nothing to scan.
	if not content:
		return

	if len(content) > int(_conf("virus_scan_max_file_size", 100 * 1024 * 1024)):
		_logger().info(f"virus_scan SKIPPED (too large): {doc.file_name} ({len(content)} bytes)")
		return

	started = time.perf_counter()
	result, engine, threats, error = _scan_bytes(content, doc.file_name or "")
	duration = time.perf_counter() - started
	file_hash = hashlib.sha256(content).hexdigest()

	_logger().info(
		f"virus_scan {result} file={doc.file_name} engine={engine} "
		f"hash={file_hash} threats={threats} duration={duration:.3f}s"
	)

	block = (
		result == INFECTED
		or (result == SUSPICIOUS and int(_conf("virus_scan_block_suspicious", 1)))
		or (result == ERROR and int(_conf("virus_scan_block_on_error", 1)))
	)
	if not block:
		return

	report = {
		"file_name": doc.file_name,
		"file_size": len(content),
		"file_hash": file_hash,
		"scan_result": result,
		"scan_engine": engine,
		"threats_found": threats,
		"error_message": error,
		"scan_duration": round(duration, 3),
		"scan_timestamp": str(now_datetime()),
		"uploaded_by": frappe.session.user,
		"attached_to": f"{doc.attached_to_doctype or ''}/{doc.attached_to_name or ''}",
	}

	# Quarantine (filesystem) and log (file logger) both survive the rollback
	# that frappe.throw triggers below. The DMS Audit Log entry is written from
	# a background job so it persists independently of this aborted transaction.
	if result in (INFECTED, SUSPICIOUS):
		_quarantine(doc, content, report)

	_record_blocked_upload(doc, report)

	if result == ERROR:
		message = _("File {0} could not be virus-scanned and was blocked for safety: {1}").format(
			frappe.bold(doc.file_name), error
		)
	else:
		message = _("Upload blocked: file {0} failed the virus scan ({1}). Threats: {2}").format(
			frappe.bold(doc.file_name), result, ", ".join(threats) or _("unknown")
		)
	frappe.throw(message, title=_("Virus Scan Failed"))


class _ContentUnreadable(Exception):
	"""Raised when the uploaded file's bytes cannot be read at all (distinct
	from a genuinely empty file), so the caller can fail closed."""


def _get_file_content(doc):
	"""Return uploaded bytes from the File doc (memory or disk).

	Returns b"" for a genuinely empty file; raises _ContentUnreadable if the
	content cannot be read (so scanning fails closed instead of open)."""
	content = getattr(doc, "content", None)
	if content is None or content == "":
		try:
			content = doc.get_content()
		except Exception as e:
			raise _ContentUnreadable(str(e))
	if isinstance(content, str):
		content = content.encode("utf-8", errors="ignore")
	return content or b""


def _scan_bytes(content, file_name):
	"""Run the best available engine. Returns (result, engine, threats, error)."""
	clamd = None
	try:
		clamd = _get_clamd()
		if clamd:
			return _scan_with_clamav(clamd, content)
	except Exception as e:
		if int(_conf("virus_scan_block_on_error", 1)):
			return ERROR, "clamav", [], str(e)
		_logger().warning(f"virus_scan ClamAV error, falling back to pattern-match: {e}")

	# ClamAV is unavailable/unreachable. If this deployment requires it, fail
	# closed instead of silently downgrading to the weak pattern-match fallback
	# (which only detects EICAR + executable magic bytes — real malware passes).
	if clamd is None and int(_conf("virus_scan_require_clamav", 0)):
		return ERROR, "clamav", [], "ClamAV engine required but unavailable/unreachable"

	return _scan_with_pattern_match(content, file_name)


def _get_clamd():
	"""Connect to a ClamAV daemon if pyclamd is installed and clamd responds."""
	try:
		import pyclamd
	except ImportError:
		return None

	socket_path = _conf("clamav_socket", "/var/run/clamav/clamd.ctl")
	if socket_path and os.path.exists(socket_path):
		cd = pyclamd.ClamdUnixSocket(socket_path)
		if cd.ping():
			return cd

	host = _conf("clamav_host", None)
	if host:
		cd = pyclamd.ClamdNetworkSocket(host, int(_conf("clamav_port", 3310)))
		if cd.ping():
			return cd
	return None


def _scan_with_clamav(clamd, content):
	scan_result = clamd.scan_stream(content)
	if scan_result is None:
		return CLEAN, "clamav", [], None
	threats = [v[1] for v in scan_result.values()]
	return INFECTED, "clamav", threats, None


def _scan_with_pattern_match(content, file_name):
	"""Pure-Python fallback: EICAR test signature + executable detection."""
	threats = []
	result = CLEAN

	if EICAR_SIGNATURE in content[:1024]:
		return INFECTED, "pattern_match", ["EICAR-Test-Signature"], None

	if int(_conf("virus_scan_block_executables", 1)):
		for signature, description in EXECUTABLE_SIGNATURES.items():
			if content.startswith(signature):
				threats.append(f"{description} content in upload: {file_name}")
				result = SUSPICIOUS

	return result, "pattern_match", threats, None


def _quarantine(doc, content, report):
	"""Copy blocked file + JSON report into the site's private quarantine folder."""
	try:
		quarantine_dir = frappe.get_site_path("private", "quarantine")
		os.makedirs(quarantine_dir, exist_ok=True)

		safe_name = "".join(
			c for c in (doc.file_name or "unnamed") if c.isalnum() or c in "._-"
		)[:100]
		stamp = now_datetime().strftime("%Y%m%d_%H%M%S")
		base = os.path.join(quarantine_dir, f"{stamp}_{report['file_hash'][:16]}_{safe_name}")

		with open(base, "wb") as f:
			f.write(content)
		with open(base + ".json", "w") as f:
			json.dump(report, f, indent=2)

		report["quarantine_path"] = base
		_logger().warning(f"virus_scan quarantined blocked file to {base}")
	except Exception:
		_logger().error(f"virus_scan failed to quarantine {doc.file_name}", exc_info=True)


def _record_blocked_upload(doc, report):
	"""Record the blocked upload.

	The file logger and quarantine JSON survive the rollback that frappe.throw
	triggers. The DMS Audit Log row is enqueued as a background job so it is
	written in its own transaction and is not rolled back with the upload.
	"""
	_logger().warning(f"virus_scan BLOCKED upload: {json.dumps(report)}")

	if (
		doc.attached_to_doctype == "Document Library"
		and doc.attached_to_name
		and frappe.db.exists("Document Library", doc.attached_to_name)
	):
		try:
			frappe.enqueue(
				"quality_dms.dms.virus_scan.write_block_audit_log",
				queue="short",
				enqueue_after_commit=False,
				document=doc.attached_to_name,
				action=f"Upload Blocked - Virus Scan {report['scan_result']}",
				user=frappe.session.user,
			)
		except Exception:
			_logger().error("virus_scan failed to enqueue audit log entry", exc_info=True)


def write_block_audit_log(document, action, user):
	"""Background job: persist a DMS Audit Log entry for a blocked upload."""
	frappe.get_doc(
		{
			"doctype": "DMS Audit Log",
			"document": document,
			"action": action,
			"user": user,
			"timestamp": now_datetime(),
		}
	).insert(ignore_permissions=True)
	frappe.db.commit()
