# PROMPT_WEB_07A_R1_REFERENCE_PROVENANCE_AND_CLOSEOUT

## Context
The stage **WEB-07A (Reference Catalog and Auto-Enrichment)** has been successfully implemented and tested. The core feature allows the system to deterministically auto-enrich product listings based on a standard reference catalog, while maintaining absolute safety for individual property overrides and restoration categories.

You are acting as the AI Assistant finalizing this stage.

## Task
Your objective is to generate the final **Provenance Documentation** and formally close out the **WEB-07A** stage.

## Instructions
1. **Review Existing Work**:
   - Briefly read `docs/REFERENCE_CATALOG_WORKFLOW.md` and `WEB_07A_REPORT.md` to understand the architecture and the rules established for the Reference Catalog.

2. **Generate Provenance Documentation**:
   - Create a document at `docs/REFERENCE_CATALOG_PROVENANCE.md`.
   - This document should explain the source of the reference data, the tier-based confidence matching rules (Tier 1: Exact Match, Tier 2: Normalized Alias Match), and the safety measures (Part/Bundle blocking, Restoration Category override safety).
   - Detail how future developers should maintain data integrity and the rules for adding new entries via API or JSON import without causing regressions.

3. **Final Closeout**:
   - Review the codebase for any lingering debug statements or loose ends from the WEB-07A implementation.
   - Print out a summary declaring WEB-07A completely closed.

## Definition of Done
- `docs/REFERENCE_CATALOG_PROVENANCE.md` exists and accurately reflects the provenance and safety architecture.
- A final confirmation message is outputted declaring the stage closed.
