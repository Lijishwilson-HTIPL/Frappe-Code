#!/usr/bin/env bash
# Apply Hephzibah custom overrides on top of submodule base code.
# Run this once after: git submodule update --init --recursive

set -e
BENCH_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PATCHES_DIR="$BENCH_DIR/patches"

echo "Applying Hephzibah customisations..."

# ERPNext: Career Inquiry — job_applicant_ref field + Python controller
cp "$PATCHES_DIR/erpnext/erpnext/setup/doctype/career_inquiry/career_inquiry.json" \
   "$BENCH_DIR/apps/erpnext/erpnext/setup/doctype/career_inquiry/career_inquiry.json"

cp "$PATCHES_DIR/erpnext/erpnext/setup/doctype/career_inquiry/career_inquiry.py" \
   "$BENCH_DIR/apps/erpnext/erpnext/setup/doctype/career_inquiry/career_inquiry.py"

# Frappe CRM: CRM Lead — website_message, primary_interest, preferred_contact, how_found_us fields
cp "$PATCHES_DIR/crm/crm/fcrm/doctype/crm_lead/crm_lead.json" \
   "$BENCH_DIR/apps/crm/crm/fcrm/doctype/crm_lead/crm_lead.json"

echo ""
echo "Copying logo files to site public files..."
SITE="${1:-mysite.local}"
SITE_DIR="$BENCH_DIR/sites/$SITE/public/files"
mkdir -p "$SITE_DIR"
cp "$BENCH_DIR/patches/assets/logo.png" "$SITE_DIR/logo.png"
cp "$BENCH_DIR/patches/assets/crm-logo.png" "$SITE_DIR/crm-logo.png"

echo "Applying logo settings to database..."

bench --site "$SITE" mariadb --execute "
INSERT INTO tabSingles (doctype, field, value) VALUES ('System Settings','brand_logo','/files/logo.png')
  ON DUPLICATE KEY UPDATE value='/files/logo.png';
INSERT INTO tabSingles (doctype, field, value) VALUES ('Navbar Settings','app_logo','/files/logo.png')
  ON DUPLICATE KEY UPDATE value='/files/logo.png';
INSERT INTO tabSingles (doctype, field, value) VALUES ('Website Settings','app_logo','/files/logo.png')
  ON DUPLICATE KEY UPDATE value='/files/logo.png';
INSERT INTO tabSingles (doctype, field, value) VALUES ('Website Settings','banner_image','/files/logo.png')
  ON DUPLICATE KEY UPDATE value='/files/logo.png';
INSERT INTO tabSingles (doctype, field, value) VALUES ('Website Settings','favicon','/files/logo.png')
  ON DUPLICATE KEY UPDATE value='/files/logo.png';
INSERT INTO tabSingles (doctype, field, value) VALUES ('Website Settings','set_banner_from_image','1')
  ON DUPLICATE KEY UPDATE value='1';
INSERT INTO tabSingles (doctype, field, value) VALUES ('FCRM Settings','brand_logo','/files/crm-logo.png')
  ON DUPLICATE KEY UPDATE value='/files/crm-logo.png';
INSERT INTO tabSingles (doctype, field, value) VALUES ('FCRM Settings','favicon','/files/crm-logo.png')
  ON DUPLICATE KEY UPDATE value='/files/crm-logo.png';
"

bench --site "$SITE" clear-cache

echo "Done. Now run: bench --site <site> migrate"
