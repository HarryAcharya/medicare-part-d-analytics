-- Phase 2 Q5: Therapeutic class spend composition, 2019 vs 2023.
--
-- Buckets each drug (by Gnrc_Name) into a therapeutic class via keyword
-- matching, then tracks dollar growth and share-of-Part-D shift across
-- the two endpoints of the data window.
--
-- METHODOLOGY: keyword-based, not from an authoritative taxonomy
-- (AHFS / ATC / USP). Drugs not matched fall into 'Other'. Expect
-- 10-20% of total spend to land there. For clinical-grade reporting,
-- a proper class taxonomy lookup table would be loaded separately.
--
-- Diabetes deliberately split into 4 subclasses (GLP-1, SGLT-2, Insulin,
-- Other Oral) to make the cardiometabolic story visible. Other major
-- classes kept at parent level.
--
-- Mftr_Name = 'Overall' filter applied per Phase 1 grain finding.

WITH classified AS (
    SELECT
        year,
        Tot_Spndng,
        CASE
            -- DIABETES (split into subclasses)
            WHEN LOWER(Gnrc_Name) IN (
                    'semaglutide', 'tirzepatide', 'dulaglutide',
                    'liraglutide', 'exenatide', 'exenatide microspheres')
                THEN 'Diabetes - GLP-1'
            WHEN LOWER(Gnrc_Name) IN (
                    'empagliflozin', 'dapagliflozin propanediol', 'dapagliflozin',
                    'canagliflozin', 'ertugliflozin pidolate',
                    'empagliflozin/metformin hcl', 'empagliflozin/linagliptin')
                THEN 'Diabetes - SGLT-2'
            WHEN LOWER(Gnrc_Name) LIKE '%insulin%'
                THEN 'Diabetes - Insulin'
            WHEN LOWER(Gnrc_Name) LIKE 'sitagliptin%'
                 OR LOWER(Gnrc_Name) LIKE 'linagliptin%'
                 OR LOWER(Gnrc_Name) LIKE 'saxagliptin%'
                 OR LOWER(Gnrc_Name) LIKE 'alogliptin%'
                 OR LOWER(Gnrc_Name) LIKE 'metformin%'
                 OR LOWER(Gnrc_Name) IN ('glipizide', 'glimepiride',
                                         'pioglitazone hcl', 'glyburide')
                THEN 'Diabetes - Oral (legacy)'

            -- CARDIOVASCULAR
            WHEN LOWER(Gnrc_Name) IN ('apixaban', 'rivaroxaban', 'warfarin sodium',
                    'dabigatran etexilate mesylate', 'edoxaban tosylate',
                    'clopidogrel bisulfate', 'ticagrelor', 'prasugrel hcl')
                THEN 'CV - Anticoag/Antiplatelet'
            WHEN LOWER(Gnrc_Name) LIKE '%statin%'
                 OR LOWER(Gnrc_Name) LIKE 'ezetimibe%'
                THEN 'CV - Cholesterol/Statin'
            WHEN LOWER(Gnrc_Name) IN ('sacubitril/valsartan', 'eplerenone', 'spironolactone',
                    'lisinopril', 'losartan potassium', 'valsartan',
                    'amlodipine besylate', 'metoprolol tartrate', 'metoprolol succinate',
                    'carvedilol', 'olmesartan medoxomil', 'atenolol',
                    'hydrochlorothiazide', 'furosemide', 'irbesartan',
                    'isosorbide mononitrate', 'isosorbide dinitrate',
                    'lisinopril/hydrochlorothiazide',
                    'losartan potassium/hydrochlorothiazide')
                THEN 'CV - BP/HF/Other'

            -- RESPIRATORY
            WHEN LOWER(Gnrc_Name) LIKE '%fluticasone%'
                 OR LOWER(Gnrc_Name) LIKE '%budesonide%'
                 OR LOWER(Gnrc_Name) LIKE '%tiotropium%'
                 OR LOWER(Gnrc_Name) LIKE '%umeclidin%'
                 OR LOWER(Gnrc_Name) LIKE '%salmeterol%'
                 OR LOWER(Gnrc_Name) LIKE '%formoterol%'
                 OR LOWER(Gnrc_Name) LIKE '%albuterol%'
                 OR LOWER(Gnrc_Name) LIKE '%ipratropium%'
                 OR LOWER(Gnrc_Name) LIKE '%montelukast%'
                 OR LOWER(Gnrc_Name) LIKE '%mometasone%'
                THEN 'Respiratory'

            -- AUTOIMMUNE / BIOLOGIC
            WHEN LOWER(Gnrc_Name) LIKE '%adalimumab%'
                 OR LOWER(Gnrc_Name) LIKE '%infliximab%'
                 OR LOWER(Gnrc_Name) LIKE '%etanercept%'
                 OR LOWER(Gnrc_Name) LIKE '%ustekinumab%'
                 OR LOWER(Gnrc_Name) LIKE '%secukinumab%'
                 OR LOWER(Gnrc_Name) LIKE '%ixekizumab%'
                 OR LOWER(Gnrc_Name) LIKE '%risankizumab%'
                 OR LOWER(Gnrc_Name) LIKE '%guselkumab%'
                 OR LOWER(Gnrc_Name) LIKE '%tofacitinib%'
                 OR LOWER(Gnrc_Name) LIKE '%baricitinib%'
                 OR LOWER(Gnrc_Name) LIKE '%upadacitinib%'
                 OR LOWER(Gnrc_Name) IN ('certolizumab pegol', 'golimumab', 'apremilast')
                THEN 'Autoimmune/Biologic'

            -- ONCOLOGY (oral; infused chemo is mostly Part B not D)
            WHEN LOWER(Gnrc_Name) IN ('lenalidomide', 'pomalidomide', 'ibrutinib',
                    'palbociclib', 'ribociclib succinate', 'abemaciclib',
                    'enzalutamide', 'abiraterone acetate', 'imatinib mesylate',
                    'dasatinib', 'nilotinib hcl', 'ruxolitinib phosphate',
                    'acalabrutinib', 'venetoclax', 'olaparib', 'osimertinib mesylate',
                    'apalutamide', 'darolutamide', 'cabozantinib s-malate',
                    'lenvatinib mesylate', 'sunitinib malate', 'pazopanib hcl',
                    'sorafenib tosylate')
                 OR LOWER(Gnrc_Name) LIKE '%anastrozole%'
                 OR LOWER(Gnrc_Name) LIKE '%letrozole%'
                 OR LOWER(Gnrc_Name) LIKE '%tamoxifen%'
                 OR LOWER(Gnrc_Name) LIKE '%exemestane%'
                THEN 'Oncology (oral)'

            -- HIV / ANTIVIRAL
            WHEN LOWER(Gnrc_Name) LIKE '%bictegrav%'
                 OR LOWER(Gnrc_Name) LIKE '%dolutegravir%'
                 OR LOWER(Gnrc_Name) LIKE '%raltegravir%'
                 OR LOWER(Gnrc_Name) LIKE '%tenofov%'
                 OR LOWER(Gnrc_Name) LIKE '%emtricitab%'
                 OR LOWER(Gnrc_Name) LIKE '%darunavir%'
                 OR LOWER(Gnrc_Name) LIKE '%rilpivirine%'
                 OR LOWER(Gnrc_Name) LIKE '%efavirenz%'
                 OR LOWER(Gnrc_Name) LIKE '%abacavir%'
                 OR LOWER(Gnrc_Name) LIKE '%sofosbuvir%'
                 OR LOWER(Gnrc_Name) LIKE '%glecaprevir%'
                 OR LOWER(Gnrc_Name) LIKE '%ledipasvir%'
                 OR LOWER(Gnrc_Name) LIKE 'valacyclovir%'
                 OR LOWER(Gnrc_Name) LIKE 'acyclovir%'
                THEN 'HIV/Antiviral'

            -- CNS / PSYCHIATRIC / NEURO
            WHEN LOWER(Gnrc_Name) IN ('sertraline hcl', 'escitalopram oxalate',
                    'duloxetine hcl', 'venlafaxine hcl', 'bupropion hcl',
                    'fluoxetine hcl', 'citalopram hbr', 'paroxetine hcl',
                    'mirtazapine', 'trazodone hcl',
                    'aripiprazole', 'olanzapine', 'risperidone',
                    'quetiapine fumarate', 'lurasidone hcl', 'ziprasidone hcl',
                    'donepezil hcl', 'memantine hcl', 'rivastigmine',
                    'lamotrigine', 'levetiracetam', 'topiramate',
                    'gabapentin', 'pregabalin', 'oxcarbazepine',
                    'divalproex sodium', 'carbamazepine',
                    'methylphenidate hcl', 'lisdexamfetamine dimesylate',
                    'amphetamine/dextroamphetamine', 'atomoxetine hcl',
                    'glatiramer acetate', 'dimethyl fumarate',
                    'teriflunomide', 'fingolimod hcl', 'ocrelizumab')
                THEN 'CNS/Psychiatric/Neuro'

            -- PAIN / OPIOID
            WHEN LOWER(Gnrc_Name) LIKE 'oxycodone%'
                 OR LOWER(Gnrc_Name) LIKE 'hydrocodone%'
                 OR LOWER(Gnrc_Name) LIKE 'morphine%'
                 OR LOWER(Gnrc_Name) LIKE 'fentanyl%'
                 OR LOWER(Gnrc_Name) LIKE 'tramadol%'
                 OR LOWER(Gnrc_Name) LIKE 'methadone%'
                 OR LOWER(Gnrc_Name) LIKE 'buprenorphine%'
                 OR LOWER(Gnrc_Name) LIKE 'hydromorphone%'
                 OR LOWER(Gnrc_Name) LIKE 'tapentadol%'
                THEN 'Pain/Opioid'

            -- GI
            WHEN LOWER(Gnrc_Name) LIKE '%omeprazole%'
                 OR LOWER(Gnrc_Name) LIKE '%pantoprazole%'
                 OR LOWER(Gnrc_Name) LIKE '%esomeprazole%'
                 OR LOWER(Gnrc_Name) LIKE '%lansoprazole%'
                 OR LOWER(Gnrc_Name) LIKE 'mesalamine%'
                 OR LOWER(Gnrc_Name) LIKE '%vedolizumab%'
                 OR LOWER(Gnrc_Name) IN ('linaclotide', 'lubiprostone', 'famotidine')
                THEN 'GI'

            ELSE 'Other'
        END AS therapeutic_class
    FROM partd_long
    WHERE Mftr_Name = 'Overall'
),
by_class_year AS (
    SELECT
        therapeutic_class,
        SUM(CASE WHEN year = '2019' THEN Tot_Spndng END) AS spend_2019,
        SUM(CASE WHEN year = '2023' THEN Tot_Spndng END) AS spend_2023
    FROM classified
    GROUP BY therapeutic_class
),
totals AS (
    SELECT
        SUM(spend_2019) AS tot_2019,
        SUM(spend_2023) AS tot_2023
    FROM by_class_year
)
SELECT
    therapeutic_class,
    ROUND(spend_2019 / 1e9, 2)                                          AS spend_2019_b,
    ROUND(spend_2023 / 1e9, 2)                                          AS spend_2023_b,
    ROUND((spend_2023 - spend_2019) / 1e9, 2)                           AS growth_b,
    ROUND(100.0 * (spend_2023 - spend_2019) / NULLIF(spend_2019, 0), 1) AS growth_pct,
    ROUND(100.0 * spend_2019 / (SELECT tot_2019 FROM totals), 1)        AS share_2019_pct,
    ROUND(100.0 * spend_2023 / (SELECT tot_2023 FROM totals), 1)        AS share_2023_pct,
    ROUND(
        100.0 * spend_2023 / (SELECT tot_2023 FROM totals)
      - 100.0 * spend_2019 / (SELECT tot_2019 FROM totals), 1)          AS share_change_pts
FROM by_class_year
ORDER BY spend_2023 DESC;