# Generate Weekly Worksheets

1. Capture original human intent and run overrides, including the resolved `subject`, `worksheettype`, and `gates` parameters when invoked via `/generate-worksheet`.
2. Load shared and subject configuration.
3. Resolve grade, week, curriculum, sources, and confidence.
4. Create and persist one immutable canonical Worksheet Spec per approved Worksheet under the Run.
5. Record each Spec reference and fingerprint in the Run Manifest.
6. Apply the subject verifier and independent reasoning review.
7. Reconcile worksheet and key from the same spec.
8. Copy the applicable master template and render.
9. Perform targeted content QA and visual layout QA.
10. Enforce enabled gates per `config/base.yaml` `gates`; skip only the gates explicitly bypassed for this run, and record the bypass decision in the Run Manifest. Gate 2 requires persisted Spec references whether or not it is bypassed.
11. Publish approved artifacts and persist the run manifest.

