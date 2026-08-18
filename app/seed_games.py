# app/seed_games.py
"""
لیست اولیهٔ بازی‌های محبوب و پرکاربرد هر دستگاه (نه لیست کامل و آرشیوی —
عناوین قدیمی و کم‌کاربرد در این لیست نیستند). با اجرای ensure_seed_games()
هر عنوان برای هر دستگاه هم به‌صورت «لایسنس» هم «کپی» در دسترس ثبت می‌شود؛
مهدی می‌تواند هرکدوم رو از صفحهٔ «بازی‌ها» دقیق‌تر کنه (مثلاً اگه یه بازی
فقط کپی داره، لایسنسش رو از اونجا حذف کنه).
"""

SEED_GAMES = {
    "PS5": [
        "Resident Evil Requiem", "Ghost of Yōtei", "Death Stranding 2: On the Beach",
        "Clair Obscur: Expedition 33", "Elden Ring", "Elden Ring: Shadow of the Erdtree",
        "God of War Ragnarök", "Marvel's Spider-Man 2", "Marvel's Spider-Man Remastered",
        "Marvel's Spider-Man: Miles Morales", "Horizon Forbidden West", "The Last of Us Part I",
        "The Last of Us Part II Remastered", "Ghost of Tsushima Director's Cut",
        "Demon's Souls", "Ratchet & Clank: Rift Apart", "Astro Bot",
        "Final Fantasy VII Rebirth", "Final Fantasy XVI", "Baldur's Gate 3",
        "Diablo IV", "Street Fighter 6", "Tekken 8", "Mortal Kombat 1",
        "EA Sports FC 25", "EA Sports FC 26", "Call of Duty: Black Ops 6",
        "Call of Duty: Modern Warfare III", "Grand Theft Auto V", "Red Dead Redemption 2",
        "Cyberpunk 2077: Phantom Liberty", "Alan Wake 2", "Hogwarts Legacy",
        "It Takes Two", "Split Fiction", "Helldivers 2", "Dragon's Dogma 2",
        "Monster Hunter Wilds", "Monster Hunter Stories 3", "Silent Hill 2",
        "Resident Evil 4 Remake", "Resident Evil Village", "Dead Space Remake",
        "Star Wars Jedi: Survivor", "Star Wars Outlaws", "Assassin's Creed Shadows",
        "Assassin's Creed Mirage", "Metaphor: ReFantazio", "Persona 3 Reload",
        "Like a Dragon: Infinite Wealth", "Granblue Fantasy: Relink", "Nioh 3",
        "007 First Light", "Dispatch", "Crimson Desert", "Pragmata", "Hades 2",
        "Mina the Hollower", "Dragon Quest 7 Reimagined", "Saros",
        "LEGO Batman: Legacy of the Dark Knight", "Marathon", "Death Stranding",
        "Sekiro: Shadows Die Twice", "Bloodborne", "Days Gone", "Returnal",
        "Gran Turismo 7", "F1 25", "EA Sports UFC 5", "NBA 2K26", "WWE 2K25",
        "Forspoken", "Baldur's Gate 3", "Diablo IV: Vessel of Hatred",
        "No Man's Sky", "Palworld", "Sea of Thieves", "Fortnite",
    ],
    "PS4": [
        "Grand Theft Auto V", "Red Dead Redemption 2", "God of War", "God of War Ragnarök",
        "The Last of Us Part I", "The Last of Us Part II", "Marvel's Spider-Man",
        "Marvel's Spider-Man: Miles Morales", "Horizon Zero Dawn", "Horizon Forbidden West",
        "Ghost of Tsushima", "Bloodborne", "Sekiro: Shadows Die Twice", "Dark Souls III",
        "Elden Ring", "Uncharted 4: A Thief's End", "Uncharted: The Lost Legacy",
        "Days Gone", "Death Stranding", "Demon's Souls",
        "Call of Duty: Modern Warfare", "Call of Duty: Black Ops Cold War",
        "Call of Duty: Vanguard", "Battlefield 1", "Battlefield V",
        "EA Sports FC 24", "FIFA 23", "FIFA 22", "FIFA 21",
        "Cyberpunk 2077", "The Witcher 3: Wild Hunt", "Resident Evil 2 Remake",
        "Resident Evil 3 Remake", "Resident Evil 7: Biohazard", "Resident Evil Village",
        "Dead Space Remake", "Tekken 7", "Street Fighter V", "Mortal Kombat 11",
        "Injustice 2", "Batman: Arkham Knight", "Batman: Arkham Asylum",
        "Assassin's Creed Origins", "Assassin's Creed Odyssey", "Assassin's Creed Valhalla",
        "Far Cry 5", "Far Cry 6", "Watch Dogs 2", "Watch Dogs: Legion",
        "Persona 5 Royal", "Nier: Automata", "Final Fantasy VII Remake",
        "Final Fantasy XV", "Kingdom Hearts III", "Dragon Ball FighterZ",
        "Diablo III", "Diablo IV", "Minecraft", "Fortnite", "Apex Legends",
        "Gran Turismo Sport", "Gran Turismo 7", "Rocket League", "FIFA 20",
        "Star Wars Jedi: Fallen Order", "Marvel's Avengers", "Control",
        "Hitman 3", "Just Cause 4", "Mafia: Definitive Edition",
        "NBA 2K23", "NBA 2K24", "WWE 2K23", "Metal Gear Solid V: The Phantom Pain",
        "Doom Eternal", "Wolfenstein II: The New Colossus", "Borderlands 3",
        "The Crew 2", "Need for Speed Heat", "GTA San Andreas: Definitive Edition",
        "PES 2021", "Little Nightmares II", "A Plague Tale: Innocence",
    ],
    "PS3": [
        "Grand Theft Auto V", "Grand Theft Auto IV", "The Last of Us", "God of War III",
        "Uncharted 2: Among Thieves", "Uncharted 3: Drake's Deception",
        "Metal Gear Solid 4: Guns of the Patriots", "Red Dead Redemption",
        "Call of Duty: Modern Warfare 2", "Call of Duty: Black Ops",
        "FIFA 14", "Pro Evolution Soccer 2013", "Gran Turismo 5", "Gran Turismo 6",
        "Batman: Arkham City", "Assassin's Creed II", "Assassin's Creed Brotherhood",
        "Resident Evil 5", "Resident Evil 6", "Tekken Tag Tournament 2",
        "Street Fighter IV", "Mortal Kombat", "Persona 5", "Dark Souls",
        "Dark Souls II", "Demon's Souls", "Skyrim", "Fallout 3", "Fallout: New Vegas",
        "Minecraft", "Injustice: Gods Among Us", "God of War: Ascension",
        "Beyond: Two Souls", "Heavy Rain",
    ],
    "PS2": [
        "Grand Theft Auto: San Andreas", "Grand Theft Auto: Vice City",
        "God of War", "God of War II", "Shadow of the Colossus", "ICO",
        "Metal Gear Solid 2: Sons of Liberty", "Metal Gear Solid 3: Snake Eater",
        "Final Fantasy X", "Final Fantasy XII", "Resident Evil 4",
        "Pro Evolution Soccer 6", "FIFA 06", "Tekken 5", "Winning Eleven 9",
        "Need for Speed Underground 2", "Devil May Cry 3",
    ],
    "PS1": [
        "Final Fantasy VII", "Final Fantasy VIII", "Metal Gear Solid",
        "Resident Evil 2", "Crash Bandicoot", "Spyro the Dragon",
        "Tekken 3", "Gran Turismo 2",
    ],
    "Xbox Series": [
        "Halo Infinite", "Forza Horizon 5", "Forza Horizon 6", "Forza Motorsport",
        "Indiana Jones and the Great Circle", "Fable", "Avowed",
        "Starfield", "Sea of Thieves", "Gears 5", "It Takes Two", "Split Fiction",
        "Elden Ring", "Elden Ring: Shadow of the Erdtree", "Alan Wake 2",
        "Cyberpunk 2077: Phantom Liberty", "Baldur's Gate 3", "Diablo IV",
        "Monster Hunter Wilds", "Street Fighter 6", "Tekken 8", "Mortal Kombat 1",
        "EA Sports FC 25", "EA Sports FC 26", "Call of Duty: Black Ops 6",
        "Grand Theft Auto V", "Red Dead Redemption 2", "Hogwarts Legacy",
        "Assassin's Creed Shadows", "Assassin's Creed Mirage", "Star Wars Outlaws",
        "Star Wars Jedi: Survivor", "Resident Evil Village", "Resident Evil 4 Remake",
        "Dead Space Remake", "Helldivers 2", "Dragon's Dogma 2",
        "Rogue Legacy 2", "007 First Light", "Clair Obscur: Expedition 33",
        "Persona 3 Reload", "Metaphor: ReFantazio", "Like a Dragon: Infinite Wealth",
        "Minecraft", "Fortnite", "Apex Legends", "Palworld", "No Man's Sky",
    ],
    "Xbox One": [
        "Halo 5: Guardians", "Halo: The Master Chief Collection", "Forza Horizon 4",
        "Forza Motorsport 7", "Gears of War 4", "Gears 5", "Sea of Thieves",
        "Grand Theft Auto V", "Red Dead Redemption 2", "The Witcher 3: Wild Hunt",
        "Call of Duty: Modern Warfare", "Call of Duty: Black Ops Cold War",
        "FIFA 21", "FIFA 22", "Battlefield 1", "Battlefield V",
        "Minecraft", "Fortnite", "Rocket League", "Apex Legends",
        "Assassin's Creed Odyssey", "Assassin's Creed Valhalla", "Far Cry 5",
        "Resident Evil 2 Remake", "Resident Evil Village", "Cyberpunk 2077",
        "Tekken 7", "Mortal Kombat 11", "NBA 2K21", "Fallout 4",
    ],
    "Nintendo Switch": [
        "The Legend of Zelda: Breath of the Wild", "The Legend of Zelda: Tears of the Kingdom",
        "Super Mario Odyssey", "Super Mario Bros. Wonder", "Mario Kart 8 Deluxe",
        "Super Smash Bros. Ultimate", "Animal Crossing: New Horizons",
        "Splatoon 2", "Splatoon 3", "Metroid Dread", "Metroid Prime Remastered",
        "Pokémon Sword", "Pokémon Shield", "Pokémon Scarlet", "Pokémon Violet",
        "Pokémon Legends: Arceus", "Fire Emblem: Three Houses", "Fire Emblem Engage",
        "Xenoblade Chronicles 3", "Bayonetta 3", "Kirby and the Forgotten Land",
        "Luigi's Mansion 3", "Mario Party Superstars", "Mario Kart World",
        "Persona 5 Royal", "Diablo III", "Minecraft", "Fortnite",
        "It Takes Two", "Hades", "Hades 2", "Stardew Valley", "Terraria",
        "Vampire Survivors", "Shin Megami Tensei V", "Octopath Traveler",
        "Monster Hunter Rise", "Pikmin 4", "Donkey Kong Bananza",
        "Mario Kart 9", "Kirby Air Riders",
    ],
    "PSP": [
        "God of War: Chains of Olympus", "God of War: Ghost of Sparta",
        "Metal Gear Solid: Peace Walker", "Grand Theft Auto: Vice City Stories",
        "Grand Theft Auto: Liberty City Stories", "Final Fantasy VII: Crisis Core",
        "Tekken 6", "Winning Eleven / Pro Evolution Soccer",
        "Persona 3 Portable", "Monster Hunter Freedom Unite", "Patapon",
        "LocoRoco",
    ],
}


def ensure_seed_games():
    """بازی‌های SEED_GAMES را برای هر دستگاه، هم به‌صورت لایسنس هم کپی، ثبت می‌کند.
    اگه بازی‌ای که خودت قبلاً دستی اضافه کرده بودی هم‌اسم یکی از این‌ها باشه، دوباره‌کاری نمی‌شه
    (بر اساس نام بازی چک می‌شه)."""
    from .models import GameTitle, DeviceName, GamePlatformAvailability

    for device_name_str, game_names in SEED_GAMES.items():
        device_name = DeviceName.objects.filter(name=device_name_str).first()
        if not device_name:
            continue
        for game_name in game_names:
            game, _ = GameTitle.objects.get_or_create(name=game_name)
            for lic in ('license', 'copy'):
                GamePlatformAvailability.objects.get_or_create(
                    game=game, device_name=device_name, license_type=lic
                )
