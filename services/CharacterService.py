import datetime
import json
import logging
import os

from discord.ext import tasks, commands
from playwright.async_api import async_playwright, ViewportSize

from STATES import AddResult, RemoveResult

TURTLE_WOW_ARMORY_URL = "https://turtle-wow.org/armory/Nordanaar/"
CHARACTERS_FILE = "characters.json"
CHARACTERS = []


class Character:
    def __init__(self, character_name, player_id, level):
        self.character_name = character_name
        self.player_id = player_id
        self.level = level

    def to_dict(self):
        return {
            "character_name": self.character_name,
            "player_id": self.player_id,
            "level": self.level
        }

    @staticmethod
    def from_dict(data):
        return Character(
            character_name=data["character_name"],
            player_id=data["player_id"],
            level=data["level"]
        )


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

# === Add character to CHARACTERS ===
async def add_character_to_list(character_name: str, player_id: str):
    if player_id is None:
        return AddResult.NO_SUCH_PLAYER
    if any(character.character_name.lower() == character_name.lower() for character in CHARACTERS):
        return AddResult.EXISTS

    new_character = Character(character_name, player_id, level="Unknown")
    new_character.level = await get_character_level(character_name)
    if not isinstance(new_character.level, (int, float)):
        return AddResult.NO_SUCH_CHARACTER

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

# === BACKGROUND TASK === Machine is in UTC+0 that's why we are setting hour to 22
@tasks.loop(time=datetime.time(hour=22, minute=0, second=0))
async def update_characters():
    logging.info("Start task update_characters")
    for character in CHARACTERS:
        character.level = await get_character_level(character.character_name)
