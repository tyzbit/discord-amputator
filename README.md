# discord-amputator
Discord bot for posting amputated links (links with Google AMP removed)

Copy example_config.json to config.json and put in your discord bot token

"logOutput" can be "stdout", "file", or "both"

"administratorIds" is an array of user IDs for users who are able to run administrator commands (currently only !ampstatus)

"automatically_amputate" determines whether the bot auto-responds to amp links in channels it can see or if it will act on direct messages only.