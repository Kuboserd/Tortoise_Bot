
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
