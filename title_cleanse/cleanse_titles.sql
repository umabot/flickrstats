DECLARE run_id STRING DEFAULT GENERATE_UUID();
DECLARE updated_rows INT64 DEFAULT 0;

CREATE TEMP TABLE title_choices AS
-- TITLE_CHOICES_QUERY
;

IF EXISTS (SELECT 1 FROM title_choices WHERE status = 'ready') THEN
  CREATE TABLE IF NOT EXISTS
    `flickrstats-492309.flickrstats.flickrstats_titles_changed` AS
  SELECT
    CAST(NULL AS STRING) AS backup_run_id,
    CAST(NULL AS TIMESTAMP) AS backup_at,
    t.*
  FROM `flickrstats-492309.flickrstats.flickrstats_all` AS t
  WHERE FALSE;

  BEGIN TRANSACTION;

  INSERT INTO `flickrstats-492309.flickrstats.flickrstats_titles_changed`
  SELECT run_id, CURRENT_TIMESTAMP(), t.*
  FROM `flickrstats-492309.flickrstats.flickrstats_all` AS t
  JOIN title_choices AS c ON t.`Photo ID` = c.`Photo ID`
  WHERE c.status = 'ready';

  UPDATE `flickrstats-492309.flickrstats.flickrstats_all` AS t
  SET `Photo Title` = c.title
  FROM title_choices AS c
  WHERE t.`Photo ID` = c.`Photo ID`
    AND c.status = 'ready'
    AND t.`Photo Title` IS DISTINCT FROM c.title;

  SET updated_rows = @@row_count;
  COMMIT TRANSACTION;
END IF;

SELECT
  run_id,
  COUNT(*) AS candidate_count,
  COUNTIF(status = 'ready') AS cleansed_count,
  COUNTIF(status = 'no_valid_title') AS no_valid_title_count,
  COUNTIF(status = 'ambiguous') AS ambiguous_count,
  (SELECT ARRAY_AGG(`Photo ID`) FROM title_choices
   WHERE status = 'no_valid_title') AS no_valid_title_ids,
  (SELECT ARRAY_AGG(`Photo ID`) FROM title_choices
   WHERE status = 'ambiguous') AS ambiguous_ids,
  updated_rows
FROM title_choices;
