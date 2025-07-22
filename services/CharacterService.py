import json
import logging
import os

from discord import Member
from playwright.async_api import async_playwright, ViewportSize

from STATES import AddResult, RemoveResult
from model.Character import Character
from services.player import select_player_by_id, update_player_nick

TURTLE_WOW_ARMORY_URL = "https://turtle-wow.org/armory/Nordanaar/"
CHARACTERS_FILE = "characters.json"
CHARACTERS = []

# === Load character list from file ===
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


# === Save character list to file ===
def save_characters_to_file():
    logging.info("Start save_characters")
    with open(CHARACTERS_FILE, "w") as file:
        json.dump([character.to_dict() for character in CHARACTERS], file, indent=2)
    logging.info("Characters saved to file.")


# === Get character from CHARACTERS by Member.id
async def get_character_by_member(member: Member):
    for character in CHARACTERS:
        if character.player_id == member.id:
            return character
    return None


# === Add character to CHARACTERS ===
async def add_character_to_list(character_name: str, player: Member):
    if player.id is None:
        return AddResult.NO_SUCH_PLAYER
    if any(character.character_name.lower() == character_name.lower() for character in CHARACTERS):
        return AddResult.EXISTS

    new_character = Character(character_name, player.id, level="Unknown")
    new_level = await get_character_level(character_name)
    if not is_number(new_level):
        return AddResult.NO_SUCH_CHARACTER
    new_character.level = new_level

    CHARACTERS.append(new_character)
    return AddResult.ADDED


# === Remove character to CHARACTERS ===
async def remove_character_from_list(character_name: str):
    for c in CHARACTERS:
        if c.character_name.lower() == character_name.lower():
            CHARACTERS.remove(c)
            return RemoveResult.REMOVED
    return RemoveResult.NOT_EXISTS


# === CHARACTER SCRAPING FUNCTION ===
async def get_character_level(name):
    logging.info(f"Start get_character_level for: {name}")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            # Create context with realistic browser settings
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                viewport=ViewportSize(width=1280, height=720),
                java_script_enabled=True,
                locale="en-US"
            )
            page = await context.new_page()

            url = f"{TURTLE_WOW_ARMORY_URL}{name}"
            await page.goto(url, wait_until='domcontentloaded')
            await page.wait_for_selector('.level', timeout=10000)

            level_el = await page.query_selector('.level')
            level_text = (await level_el.text_content()).strip() if level_el else "Unknown"
            await browser.close()
            return level_text
    except Exception as e:
        logging.error(f"Error checking {name}: {str(e)}")
        return f"Error checking {name}: {str(e)}"


# === PRINT LIST OF THE CHARACTERS ===
async def list_character_levels():
    logging.info("Start list_character_levels")
    string_buffer = ""
    for character in CHARACTERS:
        string_buffer += f"{character.character_name} is level {character.level}.\n"
    return string_buffer


async def update_characters(members: list[Member] = None):
    logging.info("Start task update_characters")
    for character in CHARACTERS:
        new_level = await get_character_level(character.character_name)
        if is_number(new_level):
            character.level = new_level
    if members is not None:
        for character in CHARACTERS:
            member = await select_player_by_id(members, character.player_id)
            await update_player_nick(member, character)


def is_number(v):
    try:
        float(v)
        return True
    except (ValueError, TypeError):
        return False
