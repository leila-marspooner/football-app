# parser.py
import re

class SimpleParser:
    def __init__(self):
        self.players = ["Winston", "Tom", "Tommy", "Logan", "Kip", "Alex", "Leo"]
        self.actions = {
            "goal": ["goal", "goll", "scored", "scores", "goall"],
            "save": ["save", "saved", "saves", "safed"],
            "shot": ["shot", "shoots", "shooting", "shoot"],
            "pass": ["pass", "passed", "passes"],
            "tackle": ["tackle", "tackled", "tackles"]
        }

    def parse(self, text):
        """
        Parse a transcription and return a list of all detected events.
        Handles both natural language and comma-separated phrases.
        """
        if not text.strip():
            return []

        # Normalize and split into candidate phrases
        normalized = re.sub(r'[^\w\s]', ' ', text)
        sentences = [s.strip() for s in re.split(r'[.!?]+', normalized) if s.strip()]
        
        # Also try comma split if no sentence structure
        if len(sentences) == 1:
            phrases = [p.strip() for p in text.split(",") if p.strip()]
        else:
            phrases = sentences

        events = []

        for phrase in phrases:
            phrase_lower = phrase.lower()
            matched = False

            # Check each action
            for action, keywords in self.actions.items():
                for keyword in keywords:
                    # Use word boundaries to avoid partial matches
                    if re.search(r'\b' + re.escape(keyword) + r'\b', phrase_lower):
                        # Find closest player to this keyword
                        player = self._find_closest_player(phrase, keyword)
                        if player:
                            events.append({
                                "type": action,
                                "player": player,
                                "raw_text": phrase.strip(),
                                "confidence": 0.9
                            })
                            matched = True
                            break
                if matched:
                    break

            if not matched:
                events.append({
                    "type": "unknown",
                    "raw_text": phrase.strip(),
                    "confidence": 0.0
                })

        return events

    def _find_closest_player(self, phrase, keyword):
        """Find the player name closest to the keyword within the phrase."""
        keyword_pos = phrase.lower().find(keyword.lower())
        if keyword_pos == -1:
            return None

        best_player = None
        min_dist = float('inf')

        for player in self.players:
            player_pos = phrase.lower().find(player.lower())
            if player_pos != -1:
                dist = abs(player_pos - keyword_pos)
                if dist < min_dist:
                    min_dist = dist
                    best_player = player

        # Only accept if reasonably close (within 30 characters)
        return best_player if min_dist < 30 else None