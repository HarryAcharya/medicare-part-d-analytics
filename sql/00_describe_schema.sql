-- Inspect partd_long schema before writing analytical queries.
-- We need exact column names + types to write the GLP-1 probe
-- and the annual totals validation without guessing.

DESCRIBE partd_long;