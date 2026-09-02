#!/usr/bin/env python3
"""Enrich catalogue records with Wikipedia thumbnails.

Reads all batch files in data/catalogue/, for each character missing an image_url
tries to fetch a thumbnail from Wikipedia via the REST API, and writes the
updated records back to their batch files.

Wikipedia article titles are inferred from the character's name + universe/
continuity, with a manual override map for ambiguous cases.
"""
import json
import ssl
import sys
import urllib.request
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
CAT_DIR = ROOT / "data" / "catalogue"

# SSL context for macOS where certs may be missing
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

HEADERS = {"User-Agent": "HackClaude/1.0 (fan-site) python-urllib"}


# Manual overrides: catalogue id -> exact Wikipedia article title
WIKI_OVERRIDES = {
    # MCU main roster
    "iron-man": "Iron_Man_(Marvel_Cinematic_Universe)",
    "captain-america": "Captain_America_(Marvel_Cinematic_Universe)",
    "thor": "Thor_(Marvel_Cinematic_Universe)",
    "hulk": "Hulk_(Marvel_Cinematic_Universe)",
    "black-widow": "Black_Widow_(Marvel_Cinematic_Universe)",
    "hawkeye": "Hawkeye_(Marvel_Cinematic_Universe)",
    "nick-fury": "Nick_Fury_(Marvel_Cinematic_Universe)",
    "maria-hill": "Maria_Hill",
    "phil-coulson": "Phil_Coulson",
    "war-machine": "War_Machine_(Marvel_Cinematic_Universe)",
    "falcon": "Falcon_(Marvel_Cinematic_Universe)",
    "winter-soldier": "Bucky_Barnes",
    "scarlet-witch": "Wanda_Maximoff",
    "vision": "Vision_(Marvel_Cinematic_Universe)",
    "ant-man": "Ant-Man_(Marvel_Cinematic_Universe)",
    "wasp": "Wasp_(Marvel_Cinematic_Universe)",
    "doctor-strange": "Doctor_Strange_(Marvel_Cinematic_Universe)",
    "black-panther": "Black_Panther_(Marvel_Cinematic_Universe)",
    "spider-man": "Spider-Man_(Marvel_Cinematic_Universe)",
    "captain-marvel": "Captain_Marvel_(Marvel_Cinematic_Universe)",
    "shang-chi": "Shang-Chi_(Marvel_Cinematic_Universe)",
    "eternals": "Eternals_(film)",  # no single character
    "guardians": "Guardians_of_the_Galaxy_(team)",
    "starlord": "Star-Lord",
    "gamora": "Gamora_(Marvel_Cinematic_Universe)",
    "drax": "Drax_the_Destroyer",
    "rocket-raccoon": "Rocket_Raccoon",
    "groot": "Groot",
    "nebula": "Nebula_(Marvel_Cinematic_Universe)",
    "mantis": "Mantis_(Marvel_Cinematic_Universe)",
    "kraglin": "Kraglin_Obfonteri",
    "cosmo": "Cosmo_the_Spacedog",
    "adam-warlock": "Adam_Warlock",
    "loki": "Loki_(Marvel_Cinematic_Universe)",
    "hela": "Hela_(Marvel_Cinematic_Universe)",
    "valkyrie": "Valkyrie_(Marvel_Cinematic_Universe)",
    "heimdall": "Heimdall_(Marvel_Cinematic_Universe)",
    "skurge": "Skurge",
    "odin": "Odin_(Marvel_Cinematic_Universe)",
    "frigga": "Frigga_(Marvel_Cinematic_Universe)",
    "sif": "Sif_(Marvel_Cinematic_Universe)",
    "volstagg": "Volstagg",
    "fandral": "Fandral",
    "hogun": "Hogun",
    "wong": "Wong_(Marvel_Cinematic_Universe)",
    "ancient-one": "Ancient_One",
    "mordo": "Karl_Mordo",
    "christine-palmer": "Christine_Palmer",
    "jonathan-pangborn": "Jonathan_Pangborn",
    "thor-love-thunder": "Thor:_Love_and_Thunder",  # film not char
    "jane-foster": "Jane_Foster_(Marvel_Cinematic_Universe)",
    "darwin-barrera": "Darwin_Barrera",  # unlikely
    "gorr": "Gorr_the_God_Butcher",
    "zeus": "Zeus_(Marvel_Cinematic_Universe)",
    "hercules": "Hercules_(Marvel_Cinematic_Universe)",
    "ares": "Ares_(Marvel_Cinematic_Universe)",
    "ares-god": "Ares_(Marvel_Cinematic_Universe)",

    # Fox X-Men
    "wolverine": "Wolverine_(character)",
    "professor-x": "Professor_X",
    "magneto": "Magneto_(Marvel_Comics)",
    "mystique": "Mystique_(Marvel_Comics)",
    "cyclops": "Cyclops_(Marvel_Comics)",
    "jean-grey": "Jean_Grey",
    "storm": "Storm_(Marvel_Comics)",
    "rogue": "Rogue_(Marvel_Comics)",
    "gambit": "Gambit_(Marvel_Comics)",
    "beast": "Beast_(Marvel_Comics)",
    "nightcrawler": "Nightcrawler",
    "iceman": "Iceman_(Marvel_Comics)",
    "colossus": "Colossus_(Marvel_Comics)",
    "kitty-pryde": "Kitty_Pryde",
    "deadpool": "Deadpool",
    "cable": "Cable_(Marvel_Comics)",
    "bishop": "Bishop_(Marvel_Comics)",
    "psylocke": "Psylocke",
    "angel": "Angel_(Marvel_Comics)",
    "juggernaut": "Juggernaut_(character)",
    "sabretooth": "Sabretooth",
    "william-stryker": "William_Stryker",
    "jason-stryker": "Jason_Stryker",
    "bolivar-trask": "Bolivar_Trask",
    "moira-mactaggert": "Moira_MacTaggert",
    "emma-frost": "Emma_Frost",
    "sebastian-shaw": "Sebastian_Shaw",
    "azazel": "Azazel_(Marvel_Comics)",
    "russell-aldrich": "Russell_Aldrich",
    "kayla-silverfox": "Kayla_Silverfox",
    "john-wraith": "John_Wraith",
    "agent-zero": "Agent_Zero_(Marvel_Comics)",

    # Fox Fantastic Four
    "reed-richards-ff": "Mister_Fantastic",
    "sue-storm-ff": "Invisible_Woman",
    "johnny-storm-ff": "Human_Torch",
    "ben-grimm-ff": "Thing_(comics)",
    "doctor-doom-ff": "Doctor_Doom",
    "galactus-ff": "Galactus",
    "silver-surfer-ff": "Silver_Surfer",
    "alicia-masters-ff": "Alicia_Masters",
    "franklin-storm-ff": "Franklin_Storm",

    # Raimi Spider-Man
    "spidey-maguire": "Spider-Man_(Tobey_Maguire)",
    "mj-maguire": "Mary_Jane_Watson",
    "green-goblin-raimi": "Green_Goblin_(Sam_Raimi_film_series)",
    "doctor-octopus-raimi": "Doctor_Octopus_(Sam_Raimi_film_series)",
    "harry-osborn": "Harry_Osborn",
    "sandman-raimi": "Sandman_(Marvel_Comics)",
    "eddie-brock-raimi": "Venom_(Sam_Raimi_film_series)",
    "gwen-stacy-raimi": "Gwen_Stacy",
    "aunt-may-raimi": "Aunt_May",
    "uncle-ben-raimi": "Uncle_Ben",
    "jjj-raimi": "J._Jonah_Jameson",

    # Webb Spider-Man
    "spidey-garfield": "Spider-Man_(Andrew_Garfield)",
    "gwen-stacy-webb": "Gwen_Stacy_(The_Amazing_Spider-Man_film_series)",
    "lizard-webb": "Lizard_(Marvel_Comics)",
    "electro-webb": "Electro_(Marvel_Comics)",
    "green-goblin-webb": "Green_Goblin_(The_Amazing_Spider-Man_film_series)",
    "rhino-webb": "Rhino_(Marvel_Comics)",
    "george-stacy-webb": "George_Stacy",
    "aunt-may-webb": "Aunt_May",

    # SSU
    "venom-hardy": "Venom_(Sony_film_series)",
    "venom-symbiote": "Venom_(character)",
    "carnage-ssu": "Carnage_(character)",
    "shriek-ssu": "Shriek_(Marvel_Comics)",
    "anne-weying": "Anne_Weying",
    "morbius": "Morbius_(character)",
    "milo-morbius": "Milo_Morbius",
    "kraven-hunter": "Kraven_the_Hunter",
    "calypso-ssu": "Calypso_(Marvel_Comics)",
    "rhino-ssu": "Rhino_(Marvel_Comics)",
    "foreigner-ssu": "Foreigner_(Marvel_Comics)",
    "ribery-ssu": "Ribery_(character)",
    "madame-web": "Madame_Web",
    "ezekiel-sims": "Ezekiel_Sims",
    "julia-cornwall": "Julia_Cornwall",
    "anya-corazon": "Anya_Corazon",
    "mattie-franklin": "Mattie_Franklin",

    # Netflix Marvel
    "matt-murdock-daredevil": "Daredevil_(Marvel_Cinematic_Universe)",
    "karen-page": "Karen_Page",
    "foggy-nelson": "Foggy_Nelson",
    "wilson-fisk-kingpin": "Kingpin_(Marvel_Cinematic_Universe)",
    "elektra-natchios": "Elektra_Natchios",
    "stick": "Stick_(Marvel_Cinematic_Universe)",
    "nobu-yoshioka": "Nobu_Yoshioka",
    "benjamin-poindexter-bullseye": "Bullseye_(Marvel_Cinematic_Universe)",
    "jessica-jones": "Jessica_Jones_(Marvel_Cinematic_Universe)",
    "trish-walker-patsy": "Trish_Walker",
    "kilgrave": "Kilgrave_(Marvel_Cinematic_Universe)",
    "jeri-hogarth": "Jeri_Hogarth",
    "malcolm-ducasse": "Malcolm_Ducasse",
    "nuke": "Nuke_(Marvel_Comics)",
    "luke-cage": "Luke_Cage_(Marvel_Cinematic_Universe)",
    "misty-knight": "Misty_Knight",
    "cottonmouth": "Cornell_Stokes",
    "mariah-dillard": "Mariah_Dillard",
    "diamondback": "Diamondback_(Marvel_Comics)",
    "shades": "Shades_(Marvel_Comics)",
    "danny-rand-iron-fist": "Iron_Fist_(Marvel_Cinematic_Universe)",
    "colleen-wing": "Colleen_Wing",
    "davos": "Davos_(Marvel_Cinematic_Universe)",
    "harold-meachum": "Harold_Meachum",
    "alexandra": "Alexandra_Reid",
    "claire-temple": "Claire_Temple",
    "frank-castle-punisher": "Punisher_(Marvel_Cinematic_Universe)",
    "billy-russo": "Billy_Russo_(Marvel_Cinematic_Universe)",
    "dinah-madani": "Dinah_Madani",
    "curtis-hoyle": "Curtis_Hoyle",

    # Agents of S.H.I.E.L.D.
    "phil-coulson-aos": "Phil_Coulson",
    "melinda-may": "Melinda_May",
    "daisy-johnson-quake": "Daisy_Johnson_(Marvel_Cinematic_Universe)",
    "fitz-simmons": "Leo_Fitz",
    "alphonso-mack": "Alphonso_Mackenzie",
    "yo-yo-rodriguez": "Elena_Rodriguez_(Marvel_Cinematic_Universe)",
    "grant-ward": "Grant_Ward_(Marvel_Cinematic_Universe)",
    "john-garrett": "John_Garrett_(Marvel_Cinematic_Universe)",
    "gideon-malick": "Gideon_Malick",
    "hive": "Hive_(Marvel_Cinematic_Universe)",
    "holden-radcliffe": "Holden_Radcliffe_(Marvel_Cinematic_Universe)",
    "aida": "A.I.D.A.",
    "ghost-rider-robbie": "Robbie_Reyes_(Marvel_Cinematic_Universe)",
    "daniel-sousa": "Daniel_Sousa_(Marvel_Cinematic_Universe)",
    "nathaniel-malick": "Nathaniel_Malick",
    "lincoln-campbell": "Lincoln_Campbell",
    "gable-hoover": "Gable_Hoover",
    "piper": "Piper_(Marvel_Cinematic_Universe)",
    "david-darrows": "David_Darrows",
    "robert-gonzalez": "Robert_Gonzales",
    "alijah-halen": "Alifah_Halen",
    "ellie-halbeck": "Ellie_Halbeck",
    "raina": "Raina_(Marvel_Cinematic_Universe)",

    # Legacy films
    "blade": "Blade_(New_Line_franchise_character)",
    "abraham-whistler-2004": "Abraham_Whistler",
    "karen-jenson": "Karen_Jenson",
    "abigail-whistler": "Abigail_Whistler",
    "hannibal-king": "Hannibal_King",
    "deacon-frost": "Deacon_Frost",
    "nomak": "Nomak",
    "damaskinos": "Eli_Damaskinos",
    "dracula-blade": "Dracula_(Blade:_Trinity)",
    "danica-talos": "Danica_Talos",
    "frank-castle-2004": "Frank_Castle_(2004_film_character)",
    "howard-saint": "Howard_Saint",
    "micro-2004": "Microchip_(character)",
    "frank-castle-warzone": "Frank_Castle_(Punisher:_War_Zone)",
    "jigsaw-2008": "Jigsaw_(Marvel_Comics)",
    "micro-2008": "Microchip_(character)",
    "johnny-blaze-gr": "Johnny_Blaze",
    "carter-slade": "Carter_Slade",
    "mephistopheles-gr": "Mephistopheles",
    "blackheart-gr": "Blackheart_(Marvel_Comics)",
    "matt-murdock-2003": "Daredevil_(Ben_Affleck)",
    "elektra-2003": "Elektra_Natchios",
    "bullseye-2003": "Bullseye_(Marvel_Comics)",
    "kingpin-2003": "Kingpin_(Marvel_Comics)",
    "foggy-nelson-2003": "Foggy_Nelson",
    "jack-murdock-2003": "Jack_Murdock",
    "stick-2005": "Stick_(Marvel_Comics)",
    "abby-miller": "Abby_Miller",
    "typhoid-mary-2005": "Typhoid_Mary",
    "howard-the-duck": "Howard_the_Duck",
    "beverly-switzler": "Beverly_Switzler",
    "the-overlord": "The_Overlord",
    "man-thing-2005": "Man-Thing",
    "pete-kasady": "Pete_Kasady",
    "nick-fury-1998": "Nick_Fury_(David_Hasselhoff)",
    "baron-strucker-1998": "Baron_Strucker",
    "captain-america-1990": "Captain_America_(1990_film)",
    "red-skull-1990": "Red_Skull",

    # MCU batches - Asgard
    "odin": "Odin_(Marvel_Cinematic_Universe)",
    "frigga": "Frigga_(Marvel_Cinematic_Universe)",
    "sif": "Sif_(Marvel_Cinematic_Universe)",
    "heimdall": "Heimdall_(Marvel_Cinematic_Universe)",
    "hogun": "Hogun",
    "fandral": "Fandral",
    "volstagg": "Volstagg",
    "skurge": "Skurge",
    "hela": "Hela_(Marvel_Cinematic_Universe)",
    "valkyrie": "Valkyrie_(Marvel_Cinematic_Universe)",
    "grandmaster": "Grandmaster_(Marvel_Cinematic_Universe)",
    "korg": "Korg_(Marvel_Cinematic_Universe)",
    "miek": "Miek",
    "fenris": "Fenris_Wolf",
    "hulk-thor": "Hulk_(Marvel_Cinematic_Universe)",  # duplicate
    "banner-thor": "Bruce_Banner",
    "thor-ragnarok": "Thor:_Ragnarok",  # film
    "thor-dark-world": "Thor:_The_Dark_World",  # film

    # MCU batches - Avengers
    "war-machine": "War_Machine_(Marvel_Cinematic_Universe)",
    "falcon": "Falcon_(Marvel_Cinematic_Universe)",
    "winter-soldier": "Bucky_Barnes",
    "scarlet-witch": "Wanda_Maximoff",
    "vision": "Vision_(Marvel_Cinematic_Universe)",
    "ant-man": "Ant-Man_(Marvel_Cinematic_Universe)",
    "wasp": "Wasp_(Marvel_Cinematic_Universe)",
    "hawk-eye": "Hawkeye_(Marvel_Cinematic_Universe)",

    # MCU batches - Eternals
    "sersi": "Sersi",
    "ikaris": "Ikaris",
    "thena": "Thena",
    "kingo": "Kingo_Sunen",
    "sprite": "Sprite_(Eternals)",
    "makkari": "Makkari_(comics)",
    "druig": "Druig",
    "gilgamesh": "Gilgamesh_(Eternals)",
    "phastos": "Phastos",
    "ajak": "Ajak",
    "kro": "Kro_(Marvel_Comics)",

    # MCU batches - Guardians
    "starlord": "Star-Lord",
    "gamora": "Gamora_(Marvel_Cinematic_Universe)",
    "drax": "Drax_the_Destroyer",
    "rocket-raccoon": "Rocket_Raccoon",
    "groot": "Groot",
    "nebula": "Nebula_(Marvel_Cinematic_Universe)",
    "mantis": "Mantis_(Marvel_Cinematic_Universe)",
    "kraglin": "Kraglin_Obfonteri",
    "cosmo": "Cosmo_the_Spacedog",
    "adam-warlock": "Adam_Warlock",
    "aleita": "Aleita",
    "howard-the-duck-mcu": "Howard_the_Duck",
    "cosmo-dog": "Cosmo_the_Spacedog",

    # MCU batches - Magic
    "doctor-strange": "Doctor_Strange_(Marvel_Cinematic_Universe)",
    "wong": "Wong_(Marvel_Cinematic_Universe)",
    "ancient-one": "Ancient_One",
    "mordo": "Karl_Mordo",
    "christine-palmer": "Christine_Palmer",
    "jonathan-pangborn": "Jonathan_Pangborn",
    "clea": "Clea",
    "america-chavez": "America_Chavez",
    "scarlet-witch": "Wanda_Maximoff",
    "wv-wanda": "Wanda_Maximoff",
    "wv-vision": "Vision_(Marvel_Cinematic_Universe)",

    # MCU batches - Support
    "nick-fury": "Nick_Fury",
    "maria-hill": "Maria_Hill",
    "phil-coulson": "Phil_Coulson",
    "pepper-potts": "Pepper_Potts",
    "happy-hogan": "Happy_Hogan",
    "tony-stark": "Iron_Man_(Marvel_Cinematic_Universe)",
    "steve-rogers": "Captain_America_(Marvel_Cinematic_Universe)",
    "natasha-romanoff": "Black_Widow_(Marvel_Cinematic_Universe)",
    "clint-barton": "Hawkeye_(Marvel_Cinematic_Universe)",

    # MCU batches - Wakanda
    "tchalla": "Black_Panther_(Marvel_Cinematic_Universe)",
    "shuri": "Shuri_(Marvel_Cinematic_Universe)",
    "okoye": "Okoye_(Marvel_Cinematic_Universe)",
    "maku": "Maku",
    "nakia": "Nakia_(Marvel_Cinematic_Universe)",
    "wk-wakabi": "W'Kabi",
    "everett-ross": "Everett_Ross",
    "ramonda": "Ramonda",
    "njobu": "N'Jobu",
    "zuri": "Zuri",

    # Doomsday 30
    "dr-doom": "Doctor_Doom",
    "reed-richards": "Mister_Fantastic",
    "sue-storm": "Invisible_Woman",
    "johnny-storm": "Human_Torch",
    "ben-grimm": "Thing_(comics)",
    "silver-surfer": "Silver_Surfer",
    "galactus": "Galactus",
    "wolverine": "Wolverine_(character)",
    "storm": "Storm_(Marvel_Comics)",
    "cyclops": "Cyclops_(Marvel_Comics)",
    "jean-grey": "Jean_Grey",
    "beast": "Beast_(Marvel_Comics)",
    "professor-x": "Professor_X",
    "magneto": "Magneto_(Marvel_Comics)",
    "mystique": "Mystique_(Marvel_Comics)",
    "deadpool": "Deadpool",
    "gambit": "Gambit_(Marvel_Comics)",
    "rogue": "Rogue_(Marvel_Comics)",
    "colossus": "Colossus_(Marvel_Comics)",
    "nightcrawler": "Nightcrawler",
    "psylocke": "Psylocke",
    "bishop": "Bishop_(Marvel_Comics)",
    "cable": "Cable_(Marvel_Comics)",
    "angel": "Angel_(Marvel_Comics)",
    "iceman": "Iceman_(Marvel_Comics)",
    "juggernaut": "Juggernaut_(character)",
    "sabretooth": "Sabretooth",
    "emma-frost": "Emma_Frost",
    "thunderbird": "Thunderbird_(Marvel_Comics)",
    "sunspot": "Sunspot_(Marvel_Comics)",
}


def wiki_title_for(char):
    """Infer or look up the Wikipedia article title for a character."""
    cid = char.get("id", "")
    if cid in WIKI_OVERRIDES:
        return WIKI_OVERRIDES[cid]

    # Try to infer from sources
    for src in char.get("sources", []):
        url = src.get("url", "")
        if "en.wikipedia.org/wiki/" in url:
            # Extract title from URL
            title = url.split("/wiki/")[-1].split("#")[0].split("?")[0]
            return title.replace("_", " ")

    # Fallback: construct from name
    name = char.get("name", "") or char.get("alias", "")
    if name:
        # Clean up: replace spaces with underscores, keep parens
        return name.strip().replace(" ", "_")

    return None


def fetch_wiki_thumb(title):
    """Return (thumb_url, page_url) or (None, None)."""
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title)}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20, context=CTX) as resp:
            data = json.load(resp)
        thumb = data.get("thumbnail", {})
        thumb_url = thumb.get("source")
        page_url = f"https://en.wikipedia.org/wiki/{quote(title)}"
        return thumb_url, page_url
    except Exception as e:
        return None, None


def fetch_image(url, dest):
    """Download image to dest, return True on success."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return True
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30, context=CTX) as resp, open(dest, "wb") as f:
            f.write(resp.read())
        return True
    except Exception as e:
        print(f"  warn: download failed {dest.name}: {e}", file=sys.stderr)
        return False


def main():
    batch_files = sorted(CAT_DIR.glob("*.json"))
    total = 0
    updated = 0
    failed = 0
    skipped = 0

    for bf in batch_files:
        print(f"\n=== {bf.name} ===")
        data = json.loads(bf.read_text(encoding="utf-8"))
        chars = data.get("characters", [])
        batch_updated = 0

        for char in chars:
            total += 1
            cid = char.get("id", "")
            if char.get("image_url"):
                skipped += 1
                continue

            title = wiki_title_for(char)
            if not title:
                print(f"  {cid}: no title inferrable")
                failed += 1
                continue

            thumb_url, page_url = fetch_wiki_thumb(title)
            if not thumb_url:
                print(f"  {cid}: no thumbnail for '{title}'")
                failed += 1
                continue

            # Download to local assets/img/cat-<id>.webp
            dest = ROOT / "assets" / "img" / f"cat-{cid}.webp"
            if fetch_image(thumb_url, dest):
                # Update record with image fields
                char["image_url"] = f"../assets/img/cat-{cid}.webp"
                char["image_source_url"] = page_url
                char["image_source_name"] = "Wikipedia"
                char["image_alt"] = f"{char.get('name', cid)} portrait"
                char["image_verified"] = False  # manual verification later
                print(f"  {cid}: OK <- {title}")
                batch_updated += 1
                updated += 1
            else:
                failed += 1

        if batch_updated:
            # Write back the batch file
            bf.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"  -> updated {batch_updated} records in {bf.name}")

    print(f"\n=== SUMMARY ===")
    print(f"Total characters: {total}")
    print(f"Already had images: {skipped}")
    print(f"Successfully enriched: {updated}")
    print(f"Failed/no thumbnail: {failed}")


if __name__ == "__main__":
    main()