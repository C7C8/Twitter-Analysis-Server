CREATE TABLE analyzed_users (
  username  VARCHAR(15) PRIMARY KEY,
  fullname  VARCHAR(50),
  checked   DATETIME DEFAULT NOW()
);

CREATE OR REPLACE TABLE tweets (
  username   VARCHAR(15),
  content    VARCHAR(512),
  created    DATETIME,
  retweets   INTEGER UNSIGNED,
  favorites  INTEGER UNSIGNED,
  replies    INTEGER UNSIGNED,
  is_retweet INTEGER UNSIGNED CHECK (is_retweet = 0 OR is_retweet = 1),
  sentiment  FLOAT,
  id         BIGINT UNSIGNED PRIMARY KEY,

  CONSTRAINT fk_username
    FOREIGN KEY (username) REFERENCES analyzed_users (username)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

  INDEX username_index (username DESC),
  INDEX created_index (created DESC),
  INDEX id_index (id DESC)
);

CREATE OR REPLACE TABLE chains (
  username   VARCHAR(15) PRIMARY KEY,
  chain      LONGBLOB,

  CONSTRAINT fk_uname
    FOREIGN KEY (username) REFERENCES analyzed_users (username)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);

-- VIEWS
CREATE OR REPLACE VIEW tweets_hourly AS (
  SELECT
    username,
    STR_TO_DATE(DATE_FORMAT(created, '%c:%e:%Y:%H'), '%c:%e:%Y:%H') AS created,
    COUNT(*)                                                        AS total,
    SUM(LENGTH(content))                                            AS total_len,
    AVG(LENGTH(content))                                            AS avg_len,
    STDDEV(LENGTH(content))                                         AS stdev_len,
    AVG(sentiment)                                                  AS avg_sent,
    STDDEV(sentiment)                                               AS stdev_sent
  FROM tweets
  WHERE is_retweet = 0
  GROUP BY username, created
  ORDER BY tweets.created DESC
);

CREATE OR REPLACE VIEW tweets_hourly_by_day AS (
  SELECT
    username,
    HOUR(created)           AS t_hour,
    WEEKDAY(created)        AS t_day,
    COUNT(*)                AS total,
    SUM(LENGTH(content))    AS total_len,
    AVG(LENGTH(content))    AS avg_len,
    STDDEV(LENGTH(content)) AS stdev_len,
    AVG(sentiment)          AS avg_sent,
    STDDEV(sentiment)       AS stdev_sent
  FROM tweets
  WHERE is_retweet = 0
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
    STDDEV(LENGTH(content)) AS stdev_len,
    AVG(sentiment)          AS avg_sent,
    STDDEV(sentiment)       AS stdev_sent
  FROM tweets
  WHERE is_retweet = 0
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
    STDDEV(LENGTH(content)) AS stdev_len,
    AVG(sentiment)          AS avg_sent,
    STDDEV(sentiment)       AS stdev_sent
  FROM tweets
  WHERE is_retweet = 0
  GROUP BY username, t_date
  ORDER BY t_date DESC
);

CREATE OR REPLACE VIEW tweets_weekly AS (
  SELECT
    username,
    WEEKDAY(created)        AS t_weekday,
    COUNT(*)                AS total,
    SUM(LENGTH(content))    AS total_len,
    AVG(LENGTH(content))    AS avg_len,
    STDDEV(LENGTH(content)) AS stdev_len,
    AVG(sentiment)          AS avg_sent,
    STDDEV(sentiment)       AS stdev_sent
  FROM tweets
  WHERE is_retweet = 0
  GROUP BY username, t_weekday
  ORDER BY t_weekday ASC
);

CREATE OR REPLACE VIEW tweets_all AS (
  SELECT
    username,
    COUNT(*)                AS total,
    SUM(LENGTH(content))    AS total_len,
    AVG(LENGTH(content))    AS avg_len,
    STDDEV(LENGTH(content)) AS stdev_len,
    AVG(sentiment)          AS avg_sent,
    STDDEV(sentiment)       AS stdev_sent
  FROM tweets
  WHERE is_retweet = 0
  GROUP BY username
);
