import discord
from discord.ext import commands
import time
import shutil
import os
from os import path
from important import data_filepath, data_backup_filepath

async def perform_message_cleanup(bot):
  if not path.exists(data_filepath):
    if not path.exists(data_backup_filepath):
      restore_backup()
    else:
      init_storage()

  with open(data_filepath, "r") as f:
    file_data = f.readlines()

  for line_number, line_data in enumerate(file_data):
    message_data = line_data.split(":")
    time_to_remove = message_data.pop()
    if float(time_to_remove) < time.time():
      channel_id = int(message_data.pop())
      message_id = int(message_data.pop())
      channel = await bot.fetch_channel(channel_id)
      message = await channel.fetch_message(message_id)
      print(message.content)
      await message.delete()
      file_data.pop(line_number)

  overwrite_raid_tracker(file_data)

def overwrite_raid_tracker(file_data):
  backup_raid_file()
  with open(data_filepath, "w") as f:
    f.writelines(file_data)


def update_raid_tracker(message, remove_after_seconds = 0):
  absolute_time_to_remove = remove_after_seconds + time.time()
  data_to_write = str(message.id) + ":" + str(message.channel.id) + ":" + str(absolute_time_to_remove) + "\n"
  backup_raid_file()
  with open(data_filepath, "a+") as f:
    f.write(data_to_write)

def backup_raid_file():
  shutil.copyfile(data_filepath, data_backup_filepath)

def restore_backup():
  shutil.copyfile(data_backup_filepath, data_filepath)

def init_storage():
  with open(data_filepath, "w") as f:
    f.write("")
  with open(data_backup_filepath, "w") as f:
    f.write("")
