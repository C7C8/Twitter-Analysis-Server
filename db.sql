CREATE TABLE analyzed_users (
  username  VARCHAR(15) PRIMARY KEY,
  fullname  VARCHAR(50)
);

CREATE TABLE tweets (
  username   VARCHAR(15),
  source     VARCHAR(24),
  content    VARCHAR(384),
  created    DATETIME,
  rewteets   INTEGER UNSIGNED,
  favorites  INTEGER UNSIGNED,
  is_retweet INTEGER UNSIGNED CHECK (is_retweet = 0 OR is_retweet = 1),
  id         BIGINT UNSIGNED PRIMARY KEY,

  CONSTRAINT fk_username
    FOREIGN KEY (username) REFERENCES analyzed_users (username)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

  INDEX created_index (created DESC),
  INDEX id_index (id DESC)
);

-- VIEWS
CREATE OR REPLACE VIEW tweets_hourly AS (
  SELECT
    username,
    STR_TO_DATE(DATE_FORMAT(created, '%c:%e:%Y:%H'), '%c:%e:%Y:%H') AS created,
    COUNT(*)                                                        AS total,
    SUM(LENGTH(content))                                            AS total_len,
    AVG(LENGTH(content))                                            AS avg_len,
    STDDEV(LENGTH(content))                                         AS stdev_len
  FROM tweets
  WHERE is_retweet = 0 AND
    source = 'Twitter for iPhone' AND
    YEAR(created) >= 2015
  GROUP BY username, created
  ORDER BY tweets.created DESC
);

CREATE OR REPLACE VIEW tweets_hourly_by_day AS (
  SELECT
    username,
    HOUR(created)           AS t_hour,
    DAYOFWEEK(created)      AS t_day,
    COUNT(*)                AS total,
    SUM(LENGTH(content))    AS total_len,
    AVG(LENGTH(content))    AS avg_len,
    STDDEV(LENGTH(content)) AS stdev_len
  FROM tweets
  WHERE is_retweet = 0 AND
    source = 'Twitter for iPhone' AND
    YEAR(created) >= 2015
  GROUP BY username, t_hour, t_day
  ORDER BY t_day ASC, t_hour ASC
);

CREATE OR REPLACE VIEW tweets_hourly_total AS (
  SELECT
    username,
    HOUR(created)           AS t_hour,
    COUNT(*)                AS total,
    SUM(LENGTH(content))    AS total_len,
    AVG(LENGTH(content))    AS avg_len,
    STDDEV(LENGTH(content)) AS stdev_len
  FROM tweets
  WHERE is_retweet = 0 AND
    source = 'Twitter for iPhone' AND
    YEAR(created) >= 2015
  GROUP BY username, t_hour
  ORDER BY t_hour ASC
);

CREATE OR REPLACE VIEW tweets_daily AS (
  SELECT
    username,
    DATE(created)           AS t_date,
    COUNT(*)                AS total,
    SUM(LENGTH(content))    AS total_len,
    AVG(LENGTH(content))    AS avg_len,
    STDDEV(LENGTH(content)) AS stdev_len
  FROM tweets
  WHERE is_retweet = 0 AND
    source = 'Twitter for iPhone' AND
    YEAR(created) >= 2015
  GROUP BY username, t_date
  ORDER BY t_date DESC
);

SELECT * FROM tweets WHERE
  (source = 'Twitter for iPhone' OR source = 'Twitter for Android') AND
    is_retweet = 0 AND
    YEAR(created) >= 2015
ORDER BY created DESC;