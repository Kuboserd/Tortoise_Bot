import json
import logging
import os

from discord import Member

from STATES import AddResult, RemoveResult
from model.Character import Character
from services.blizzard_api import BlizzardError, fetch_character
from services.player import select_player_by_id, update_player_nick

CHARACTERS_FILE = "characters.json"
CHARACTERS = []


def character_key(name: str) -> str:
    return "-".join(name.replace("-", " ").split()).casefold()


def load_characters_from_file():
    logging.info("Start load_characters")
    global CHARACTERS

    if not os.path.exists(CHARACTERS_FILE):
        with open(CHARACTERS_FILE, "w") as file:
            json.dump([], file)
        CHARACTERS = []
        logging.info(f"{CHARACTERS_FILE} did not exist. Created empty file.")
        return

    with open(CHARACTERS_FILE, "r") as file:
        try:
            data = json.load(file)
            if not data:
                CHARACTERS = []
                logging.info(f"{CHARACTERS_FILE} is empty. No characters loaded.")
                return
            CHARACTERS = [Character.from_dict(character) for character in data]
            logging.info(f"Loaded {len(CHARACTERS)} characters from file.")
        except json.JSONDecodeError:
            CHARACTERS = []
            logging.warning(f"{CHARACTERS_FILE} is invalid JSON or empty. Initialized empty character list.")


def save_characters_to_file():
    logging.info("Start save_characters")
    with open(CHARACTERS_FILE, "w") as file:
        json.dump([character.to_dict() for character in CHARACTERS], file, indent=2)
    logging.info("Characters saved to file.")


async def get_character_by_member(member: Member):
    for character in CHARACTERS:
        if character.player_id == member.id:
            return character
    return None


async def add_character_to_list(character_name: str, player: Member):
    if player is None or player.id is None:
        return AddResult.NO_SUCH_PLAYER
    if any(character_key(character.character_name) == character_key(character_name) for character in CHARACTERS):
        return AddResult.EXISTS

    try:
        profile = await fetch_character(character_name)
    except BlizzardError as error:
        logging.error(f"Failed to look up {character_name}: {error}")
        return AddResult.API_ERROR
    if profile is None or "level" not in profile:
        return AddResult.NO_SUCH_CHARACTER

    canonical_name = profile.get("name_search") or character_name
    if any(character_key(character.character_name) == character_key(canonical_name) for character in CHARACTERS):
        return AddResult.EXISTS

    CHARACTERS.append(Character(canonical_name, player.id, level=str(profile["level"])))
    save_characters_to_file()
    return AddResult.ADDED


async def remove_character_from_list(character_name: str):
    for character in CHARACTERS:
        if character_key(character.character_name) == character_key(character_name):
            CHARACTERS.remove(character)
            save_characters_to_file()
            return RemoveResult.REMOVED
    return RemoveResult.NOT_EXISTS


async def list_character_levels():
    logging.info("Start list_character_levels")
    string_buffer = ""
    for character in CHARACTERS:
        string_buffer += f"{character.character_name} is level {character.level}.\n"
    return string_buffer


async def update_characters(members: list[Member] = None):
    logging.info("Start task update_characters")
    for character in CHARACTERS:
        try:
            profile = await fetch_character(character.character_name)
        except BlizzardError as error:
            logging.error(f"Failed to update {character.character_name}: {error}")
            continue
        if profile is None or "level" not in profile:
            logging.warning(
                f"No Forever profile for {character.character_name}. "
                "Blizzard publishes characters from level 10, after they log out."
            )
            continue
        character.level = str(profile["level"])
        if profile.get("name_search"):
            character.character_name = profile["name_search"]

    save_characters_to_file()

    if members is not None:
        for character in CHARACTERS:
            member = await select_player_by_id(members, character.player_id)
            await update_player_nick(member, character)
