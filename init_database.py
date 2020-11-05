import asyncio
import asyncpg
from important import password

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

async def main():

  conn = await asyncpg.connect(database='pogo_raid_bot',
                               port=5432,
                               host='localhost',
                               user='pi',
                               password=password)

  await conn.execute(raid_counter_table)

asyncio.get_event_loop().run_until_complete(main())
