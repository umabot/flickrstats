WITH candidates AS (
  SELECT `Photo ID`
  FROM `flickrstats-492309.flickrstats.flickrstats_all`
  WHERE `Photo ID` IS NOT NULL
  GROUP BY `Photo ID`
  HAVING COUNT(DISTINCT `Photo Title`) > 1
),
valid_titles AS (
  SELECT
    t.`Photo ID`,
    t.`Photo Title`,
    DENSE_RANK() OVER (
      PARTITION BY t.`Photo ID` ORDER BY t.updated_at DESC
    ) AS title_rank
  FROM `flickrstats-492309.flickrstats.flickrstats_all` AS t
  JOIN candidates AS c ON t.`Photo ID` = c.`Photo ID`
  WHERE t.updated_at IS NOT NULL
    AND t.`Photo Title` IS NOT NULL
    AND NOT STARTS_WITH(t.`Photo Title`, 'PXL')
    AND NOT STARTS_WITH(t.`Photo Title`, 'IMG')
    AND NOT STARTS_WITH(t.`Photo Title`, 'CR2')
    AND NOT STARTS_WITH(t.`Photo Title`, '20')
    AND NOT STARTS_WITH(t.`Photo Title`, 'P100')
),
latest_titles AS (
  SELECT
    `Photo ID`,
    COUNT(DISTINCT `Photo Title`) AS title_count,
    MIN(`Photo Title`) AS title
  FROM valid_titles
  WHERE title_rank = 1
  GROUP BY `Photo ID`
)
SELECT
  c.`Photo ID`,
  CASE WHEN l.title_count = 1 THEN l.title END AS title,
  CASE
    WHEN l.title_count IS NULL THEN 'no_valid_title'
    WHEN l.title_count > 1 THEN 'ambiguous'
    ELSE 'ready'
  END AS status
FROM candidates AS c
LEFT JOIN latest_titles AS l ON c.`Photo ID` = l.`Photo ID`
