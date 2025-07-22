
async def select_player(members, player_name):
    for member in members:
        username = member.name.lower() if member.name else None
        nickname = member.nick.lower() if member.nick else None
        display_name = member.display_name.lower() if member.display_name else None

        if player_name.lower() == nickname or player_name.lower() == username or player_name.lower() == display_name:
            return member.id

    return None
#
# async def update_player_nick(member, )