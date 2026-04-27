CREATE TABLE IF NOT EXISTS chats (
    chat_id BIGINT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS links (
    id        BIGSERIAL PRIMARY KEY,
    url       TEXT UNIQUE NOT NULL,
    link_type TEXT        NOT NULL,
    last_known_update TEXT,
    last_checked_at   TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS chat_links (
    chat_id BIGINT NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
    link_id BIGINT NOT NULL REFERENCES links(id)      ON DELETE CASCADE,
    tags    TEXT[] NOT NULL DEFAULT '{}',
    filters TEXT[] NOT NULL DEFAULT '{}',
    PRIMARY KEY (chat_id, link_id)
);

CREATE INDEX IF NOT EXISTS idx_links_url          ON links(url);
CREATE INDEX IF NOT EXISTS idx_chat_links_chat_id ON chat_links(chat_id);
