import logging

from discord import Member

from model.Character import Character


async def select_player_by_name(members, player_name):
    for member in members:
        username = member.name.lower() if member.name else None
        nickname = member.nick.lower() if member.nick else None
        display_name = member.display_name.lower() if member.display_name else None

        if player_name.lower() == nickname or player_name.lower() == username or player_name.lower() == display_name:
            return member

    return None


async def select_player_by_id(members, player_id):
    for member in members:
        if member.id == player_id:
            return member

    return None


async def update_player_nick(member: Member, character: Character):
    # old_nick = member.nick
    # if old_nick is None:
    #     old_nick = member.display_name
    # if old_nick is None:
    #     old_nick = member.name
    # if character.character_name in old_nick:
    #     parts = old_nick.split()
    #     old_nick = parts[-1] if parts else old_nick
    try:
        new_nick = character.character_name + " lvl" + character.level
        logging.info(f"Setting nick {new_nick} for {member.name}")
        await member.edit(nick=new_nick)
    except Exception as e:
        logging.error(f"Failed to set nickname for {character.character_name} ({member.name})")
