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

echo "Done. Now run: bench --site <site> migrate"
