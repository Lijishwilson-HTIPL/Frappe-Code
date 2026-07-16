# Copyright (c) 2026, Quality Team and contributors
"""Create/refresh the Quality Document Workflow so the signable publish flow
exists on every site (fresh installs and live), not just where a dev script
was run by hand."""

from quality_dms.dms.setup.workflow import setup_quality_document_workflow


def execute():
    setup_quality_document_workflow()
