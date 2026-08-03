import pyqrcode


def qr_base64(data, scale=4):
	"""Return a base64-encoded PNG QR code for `data`, for use in print formats.

	Usage in a Print Format (Jinja):
	    <img src="data:image/png;base64,{{ qr_base64(doc.name) }}">
	"""
	return pyqrcode.create(str(data or "")).png_as_base64_str(scale=scale, quiet_zone=1)
