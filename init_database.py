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
CREATE TABLE IF NOT EXISTS raids (
  raid_message_id BIGINT PRIMARY KEY,
  host_user_id BIGINT NOT NULL,
  guild_id BIGINT NOT NULL,
  time_to_remove TIMESTAMP NOT NULL,
  FOREIGN KEY (host_user_id)
    REFERENCES players (user_id)
);
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

RAID_LOBBY_CATEGORY = """
DROP TABLE IF EXISTS raid_lobby_category;
CREATE TABLE IF NOT EXISTS raid_lobby_category (
  guild_id BIGINT PRIMARY KEY,
  category_id BIGINT NOT NULL,
  log_channel_id BIGINT NOT NULL
)
"""

RAID_LOBBY_USER_MAP = """
DROP TABLE IF EXISTS raid_lobby_user_map;
CREATE TABLE IF NOT EXISTS raid_lobby_user_map (
  lobby_channel_id BIGINT PRIMARY KEY,
  host_user_id BIGINT NOT NULL,
  raid_message_id BIGINT NOT NULL,
  guild_id BIGINT NOT NULL,
  posted_at TIMESTAMP NOT NULL,
  delete_at TIMESTAMP NOT NULL,
  user_count INT NOT NULL,
  user_limit INT NOT NULL,
  applied_users INT NOT NULL,
  notified_users INT NOT NULL
)
"""

RAID_RECENT_PARTICIPATION_TABLE = """
DROP TABLE IF EXISTS raid_participation_table;
CREATE TABLE IF NOT EXISTS raid_participation_table (
  user_id BIGINT PRIMARY KEY,
  last_participation_time TIMESTAMP NOT NULL
)
"""

RAID_APPLICATION_USER_MAP = """
DROP TABLE IF EXISTS raid_application_user_map;
CREATE TABLE IF NOT EXISTS raid_application_user_map (
  user_id BIGINT PRIMARY KEY,
  raid_message_id BIGINT NOT NULL,
  guild_id BIGINT NOT NULL,
  is_requesting BOOL NOT NULL,
  speed_bonus_weight INT NOT NULL,
  has_been_notified BOOL NOT NULL,
  checked_in BOOL NOT NULL,
  activity_check_message_id BIGINT
)
"""
UPDATE_DATA_TYPE = """
    ALTER TABLE raid_application_user_map
    ALTER COLUMN speed_bonus_weight TYPE DOUBLE PRECISION;
"""
friend_code_table = """
  CREATE TABLE IF NOT EXISTS friend_codes (
    user_id BIGINT PRIMARY KEY,
    friend_code CHAR(12) NOT NULL,
    last_time_recalled TIMESTAMP NOT NULL
  )
"""
async def main():
  conn = await asyncpg.connect(database='pogo_raid_bot',
                               port=5432,
                               host='localhost',
                               user='pi',
                               password=PASSWORD)
  #await conn.execute(UPDATE_DATA_TYPE)
  #await conn.execute(RAID_LOBBY_CATEGORY)
  #await conn.execute(RAID_LOBBY_USER_MAP)
  #await conn.execute(RAID_RECENT_PARTICIPATION_TABLE)
  #await conn.execute(RAID_APPLICATION_USER_MAP)
  await conn.execute(friend_code_table)


asyncio.get_event_loop().run_until_complete(main())
