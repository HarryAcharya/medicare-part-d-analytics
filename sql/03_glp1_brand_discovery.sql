-- Discover ALL brand variants of every GLP-1 molecule in the dataset.
-- Filtering by Gnrc_Name (the active molecule) is more robust than brand-name
-- filtering: it catches brand variants like 'Victoza 3-Pak', 'Bydureon Pen', etc.
-- without us having to know them in advance.

SELECT DISTINCT
    Brnd_Name,
    Gnrc_Name
FROM partd_long
WHERE LOWER(Gnrc_Name) IN (
    'semaglutide',
    'tirzepatide',
    'dulaglutide',
    'liraglutide',
    'exenatide',
    'exenatide microspheres'
)
ORDER BY Gnrc_Name, Brnd_Name;