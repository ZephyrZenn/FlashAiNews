CREATE TABLE IF NOT EXISTS feeds
(
    id           INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    url          VARCHAR(255) UNIQUE NOT NULL,
    title        VARCHAR(64)         NOT NULL,
    description  VARCHAR(512)        NOT NULL,
    last_updated TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "limit"      INTEGER             NOT NULL DEFAULT 10,
    created_at   TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feed_items
(
    id          VARCHAR(128) PRIMARY KEY,
    feed_id     INTEGER      NOT NULL,
    title       VARCHAR(64)  NOT NULL,
    link        VARCHAR(255) NOT NULL,
    pub_date    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feed_item_contents
(
    id           INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    feed_item_id VARCHAR(128) NOT NULL,
    content      TEXT         NOT NULL,
    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feed_groups
(
    id         INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    title
               VARCHAR(64)  NOT NULL,
    "desc"
               VARCHAR(512) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feed_group_items
(
    id            INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    feed_group_id INTEGER NOT NULL,
    feed_id       INTEGER NOT NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_feed_items_feed_id_pub_date ON feed_items (feed_id, pub_date);
CREATE INDEX idx_feed_item_contents_feed_item_id ON feed_item_contents (feed_item_id);
CREATE INDEX idx_group_items_group_feed_id ON feed_group_items (feed_group_id, feed_id);