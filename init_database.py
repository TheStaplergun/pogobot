import asyncio
import asyncpg
from important import PASSWORD

player_table_create = """
CREATE TABLE IF NOT EXISTS players (
  user_id BIGINT PRIMARY KEY,
  friend_code CHAR(12) NOT NULL,
  Level SMALLINT NOT NULL,
  time_registered TIMESTAMP NOT NULL,
  raids_posted INT NOT NULL,
  restricted BOOL NOT NULL
);
"""

raid_table_create = """
DROP TABLE IF EXISTS raids;
CREATE TABLE IF NOT EXISTS raids (
  message_id BIGINT PRIMARY KEY,
  lobby_id BIGINT NOT NULL,
  time_registered TIMESTAMP NOT NULL,
  guild_id BIGINT NOT NULL,
  channel_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  time_to_remove TIMESTAMP NOT NULL
);
"""

raid_table_add_lobby_column = """
ALTER TABLE raids
ADD COLUMN lobby_id BIGINT;
"""

raid_anonymous_tracker = """
CREATE TABLE IF NOT EXISTS tracker (
  applicant_id BIGINT PRIMARY KEY,
  host_dm_message_id BIGINT NOT NULL,
  host_id BIGINT NOT NULL,
  raid_message_id BIGINT NOT NULL,
  FOREIGN KEY (host_id)
    REFERENCES players (user_id),
  FOREIGN KEY (applicant_id)
    REFERENCES players (user_id),
  FOREIGN KEY (raid_message_id)
    REFERENCES raids (raid_message_id)
);
"""

placeholder_database = """
CREATE TABLE IF NOT EXISTS raid_placeholder_stickies (
  channel_id BIGINT PRIMARY KEY,
  message_id BIGINT NOT NULL,
  guild_id BIGINT NOT NULL
);
"""

valid_raid_channels = """
CREATE TABLE IF NOT EXISTS valid_raid_channels (
  channel_id BIGINT PRIMARY KEY,
  guild_id BIGINT NOT NULL
);
"""
raid_counter_table = """
DROP TABLE IF EXISTS guild_raid_counters;
CREATE TABLE IF NOT EXISTS guild_raid_counters (
  guild_id BIGINT PRIMARY KEY,
  raid_counter BIGINT DEFAULT 0
);
"""

request_channel_table = """
DROP TABLE IF EXISTS valid_request_channels;
CREATE TABLE IF NOT EXISTS valid_request_channels (
  guild_id BIGINT PRIMARY KEY,
  channel_id BIGINT NOT NULL
);
"""

request_role_to_id_map = """
DROP TABLE IF EXISTS request_role_id_map;
CREATE TABLE IF NOT EXISTS request_role_id_map (
  role_id BIGINT PRIMARY KEY,
  message_id BIGINT NOT NULL,
  guild_id BIGINT NOT NULL,
  role_name VARCHAR(32)
)
"""

raid_lobby_category_table = """
CREATE TABLE IF NOT EXISTS raid_lobby_categories (
  primary_id BIGINT PRIMARY KEY,
  guild_id BIGINT NOT NULL
)
"""




async def main():
  conn = await asyncpg.connect(database='pogo_raid_bot',
                               port=5432,
                               host='localhost',
                               user='pi',
                               password=PASSWORD)

  #await conn.execute(request_channel_table)
  #await conn.execute(request_role_to_id_map)

asyncio.get_event_loop().run_until_complete(main())
