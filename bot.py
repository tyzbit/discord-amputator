#!/usr/bin/env python3
import discord
import json
import logging
import pathlib
import sys
import time
import urllib
from urlextract import URLExtract

amp_fragment = "https://www.google.com/amp/s/"

# https://stackoverflow.com/a/66683635/12948940
def remove_suffix(input_string, suffix):
    if suffix and input_string.endswith(suffix):
        return input_string[:-len(suffix)]
    return input_string

class BotState:
  def __init__(self):
    self.load_config()

  def load_config(self):
    '''
    Initializes the bot state by reading it from a file
    '''
    self.current_dir = str(pathlib.Path(__file__).resolve().parent)
    config_file = f'{current_dir}/config.json'
    try:
      with open(config_file, 'r') as read_file:
        try:
          self.config = json.load(read_file)
        except Exception as e:
          logger.error(f'Unable to read config file at {config_file}, {e}')
          sys.exit(1)
    except Exception as e:
      logger.warning(f'Config file not found at {config_file}, exiting')
      sys.exit(1)

async def post_message(target=None, text=None, embed=None):
  '''
  Sends a target (user, DM) the text string or embed provided
  '''
  if not target:
    logger.error(f'post_message called without target (channel or user)', extra={'guild': 'internal'})
  else:
    try:
      name = target.name
    except:
      name = target.recipient.name
    logger.debug(msg=f'Sending a message to {name}', extra={'guild': 'internal'})
    if embed:
      return await target.send(embed=embed)
    elif text:
      return await target.send(text)
    else:
      logger.error(f'send_dm called without text or embed', extra={'guild': 'internal'})

async def amputate(bot_state, client, extractor, message):
  '''
  Removes Google amp from links, posts an embed with the amputated link
  '''
  try:
    guild = message.guild.id
  except:
    guild = 'internal'

  config = bot_state.config
  urls = extractor.find_urls(message.content)
  amputated_urls_str = ""
  for url in urls:
    if amp_fragment in url:
      logger.info(f'Amputating URL: {url}', extra={'guild': guild})
      amputated_urls_str = f'{amputated_urls_str}{url.replace("https://www.google.com/amp/s/", "https://")}\n'
  amputated_urls_str = remove_suffix(amputated_urls_str, "\n")

  embed = discord.Embed()
  embed.color = 6591981 # cornflower blue
  embed.add_field(name='Amputated link', value=amputated_urls_str, inline=False)

  send_dm = False
  try:
    target = message.channel
    try:
      if bot_state.config['automaticallyAmputate']:
        send_dm = True
      else:
        logger.info(f'Saw a link to amputate but "automaticallyAmputate" is not true', extra={'guild': guild})
    except:
      logger.warn(f'"automaticallyAmputate" is not set', extra={'guild': guild})
  except Exception as e:
    logger.info(f'Could not get channel from message, assuming we need to DM', extra={'guild': guild})
    target = message.author
    send_dm = True
  
  if send_dm:
    await post_message(target=target, embed=embed)

async def status_command(bot_state, client, message):
  config = bot_state.config
  # only administrators can use this command
  if message.author.id not in config['administratorIds']:
    logger.debug(f'Status command called but {message.author.id} is not in administratorIds', extra={'guild': 'internal'})
  else:
    guild_list = ''
    i = 0
    for guild in client.guilds:
      if i > 0:
        guild_list = f'{guild_list}, {guild.name}'
      else:
        guild_list = f'{guild.name}'

      i = i + 1

    embed = discord.Embed()
    embed.title = 'Amputator status'
    embed.color = 16753920 # orange
    embed.add_field(name='Guild list', value=guild_list, inline=False)
    embed.add_field(name='Cached messages', value=str(len(client.cached_messages)), inline=False)
    embed.add_field(name='Private messages', value=str(len(client.private_channels)), inline=False)

    try:
      target = message.channel
    except:
      target = message.author

    await post_message(target=target, embed=embed)

def main(bot_state):
  logger.info(msg='Starting bot...', extra={'guild': 'internal'})

  discordToken = bot_state.config['discordToken']
  client = discord.Client()

  possible_commands={
    '!ampstatus': 'status_command'
  }

  @client.event
  async def on_ready():
    logger.info(msg=f'{client.user} has connected to Discord!', extra={'guild': 'internal'})
  
  @client.event
  async def on_message(message):
    if message.author == client.user:
      return

    try:
      guild = message.guild.id
    except:
      guild = 'direct'      

    for command in possible_commands:
      if message.content.split(' ')[0] == command:
        function = possible_commands[message.content.split(' ')[0]]
        call_function = globals()[function]
        logger.debug(f'Calling {function}', extra={'guild': guild})
        await call_function(bot_state, client, message)
    
    if amp_fragment in message.content:
      await amputate(bot_state, client, extractor, message)

  @client.event
  async def on_guild_join(guild):
    logger.info(f'Joined guild {guild.name}', extra={'guild': guild.id})
  
  @client.event
  async def on_guild_remove(guild):
    logger.info(f'Left guild {guild.name}', extra={'guild': guild.id})

  client.run(discordToken)

if __name__ == '__main__':
  current_dir = pathlib.Path(__file__).resolve().parent

  # Init state
  bot_state = BotState()
  config = bot_state.config

  time.tzset()

  # Set up logging to console and file
  logger = logging.getLogger('bot')
  formatter = logging.Formatter('%(asctime)s - %(guild)s - %(levelname)s - %(message)s')
  if config['logOutput'] == "file" or config['logOutput'] == "both":
    fh = logging.FileHandler(str(current_dir) + '/bot.log')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
  if config['logOutput'] == "stdout" or config['logOutput'] == "both":
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

  # Set loglevel
  level_config = {
    'debug': logging.DEBUG,
    'info': logging.INFO, 
    'warn': logging.WARNING,
    'error': logging.ERROR
  }
  if 'logLevel' in config:
    loglevel = config['logLevel']
    logger.setLevel(level_config[loglevel])
    logger.info(msg=f'Logging set to {config["logLevel"]}...', extra={'guild': 'internal'})
  else:
    logger.setLevel(logging.WARN)
    logger.warn(msg=f'Logging set to warn...', extra={'guild': 'internal'})

  if 'discordToken' not in config:
    logger.error(msg='\'discordToken\' is not set in config', extra={'guild': 'internal'})
    sys.exit(1)

  discordToken = config['discordToken']
  extractor = URLExtract()
  main(bot_state)