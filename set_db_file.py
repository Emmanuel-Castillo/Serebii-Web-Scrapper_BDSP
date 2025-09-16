import sqlite3

# Connect (creates file if it doesn't exist)
conn = sqlite3.connect("pokedex.db")
cur = conn.cursor()

# Region table
cur.execute("" \
"CREATE TABLE IF NOT EXISTS Table(" \
"id INTEGER PRIMARY KEY AUTOINCREMENT," \
"name TEXT NOT NULL," \
"parentRegionId)")

# Example Game table (matches the @Entity Game)
cur.execute("" \
"CREATE TABLE IF NOT EXISTS Game(" \
"id INTEGER PRIMARY KEY AUTOINCREMENT," \
"name TEXT NOT NULL," \
"generation INTEGER NOT NULL," \
"mainPokedexId INTEGER NOT NULL" \
"versionGroupId INTEGER NOT NULL" \
"FOREIGN KEY (mainPokedexId) REFERENCES Pokedex(id))")

# (name, generation, mainPokedexId, versionGroupId)
games = [
    ("Pokémon Red", 1, 1, 1),
    ("Pokémon Blue", 1, 1, 1),
    ("Pokémon Yellow", 1, 1, 1),
    ("Pokémon Gold", 2, 2),
    ("Pokémon Silver", 2, 2),
    ("Pokémon Crystal", 2, 2),
    ("Pokémon Ruby", 3, 3),
    ("Pokémon Sapphire", 3, 3),
    ("Pokémon Emerald", 3, 3),
    ("Pokémon FireRed", 3, 1),
    ("Pokémon LeafGreen", 3, 1),
    ("Pokémon Diamond", 4, 4),
    ("Pokémon Pearl", 4, 4),
    ("Pokémon Platinum", 4, 5),
    ("Pokémon HeartGold", 4, 6),
    ("Pokémon SoulSilver", 4, 6),
    ("Pokémon Black", 5, 7),
    ("Pokémon White", 5, 7),
    ("Pokémon Black 2", 5, 8),
    ("Pokémon White 2", 5, 8),
    ("Pokémon X", 6, 9),
    ("Pokémon Y", 6, 9),
    ("Pokémon Omega Ruby", 6, 13),
    ("Pokémon Alpha Sapphire", 6, 13),
    ("Pokémon Sun", 7, 14),
    ("Pokémon Moon", 7, 14),
    ("Pokémon Ultra Sun", 7, 19),
    ("Pokémon Ultra Moon", 7, 19),
    ("Pokémon Let's Go: Pikachu!", 7, 24),
    ("Pokémon Let's Go: Eevee!", 7, 24),
    ("Pokémon Sword", 8, 25),
    ("Pokémon Shield", 8, 25),
    ("Pokémon Brilliant Diamond", 8, 4),
    ("Pokémon Shining Pearl", 8, 4),
    ("Pokémon Legends: Arceus", 8, 28),
    ("Pokémon Scarlet", 9, 29),
    ("Pokémon Violet", 9, 29),
]

cur.executemany("INSERT INTO Game (name, generation, mainPokedexId, versionGroupId) VALUES (?, ?, ?, ?)", games)

query = cur.execute("SELECT * FROM Game")
print(query.fetchall())

# Pokedex Table
cur.execute("" \
"CREATE TABLE IF NOT EXISTS Pokedex(" \
"id INTEGER PRIMARY KEY AUTOINCREMENT," \
"name TEXT NOT NULL," \
"regionId INTEGER NOT NULL," \
"versionGroupId INTEGER NOT NULL" \
"parentPokedexId INTEGER" \
"FOREIGN KEY (parentPokedexId) REFERENCES Pokedex(id)" \
"FOREIGN KEY (regionId) REFERENCES Region(id)" \
"FOREIGN KEY (versionGroupId) REFERENCES Game(versionGroupId))")

# (name, regionId, versionGroupId, parentPokedexId?)
pokedexes = [
    ("Kanto Pokédex", 1)
]

