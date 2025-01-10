# path: .app/tools/game_info.py

from .characters import available_characters, game_type
from .filter_keys import get_filter_keys

game_info = {
    "doapp": {
        "game_id": "doapp",
        "original_rom_name": "doapp.zip",
        "sha256_checksum": "d95855c7d8596a90f0b8ca15725686567d767a9a3f93a8896b489a160e705c4e",
        "search_keywords": [
            "DEAD OR ALIVE ++ [JAPAN]", "dead-or-alive-japan", "80781", "wowroms"
        ],
        "resolution": (480, 512, 3),  # (Height, Width, Channels)
        "moves": [
            "No-Move", "Left", "Left+Up", "Up", "Up+Right",
            "Right", "Right+Down", "Down", "Down+Left"
        ],
        "attacks": [
            "No-Attack", "Hold", "Punch", "Kick", "Hold+Punch",
            "Hold+Kick", "Punch+Kick", "Hold+Punch+Kick"
        ],
        "max_difficulty": 4,
        "num_characters": 11,
        "max_outfits": 4,
        "num_stages": 8,
        "game_type": game_type.get("doapp", "unknown"),
        "characters": available_characters.get("doapp", []),
        "action_spaces": {
            "discrete": 16,  # 9 moves + 8 attacks - 1 no-op double count
            "multi_discrete": 72  # 9 moves * 8 attacks
        },
        "observation_space": {
            "global": {
                "frame": {
                    "type": "Box",
                    "value_range": [0, 255],
                    "description": "Latest game frame (RGB pixel screen)"
                },
                "stage": {
                    "type": "Box",
                    "value_range": [1, 8],
                    "description": "Current stage of the game"
                },
                "timer": {
                    "type": "Box",
                    "value_range": [0, 40],
                    "description": "Round time remaining"
                }
            },
            "player_specific": {
                "side": {
                    "type": "Discrete (Binary)",
                    "value_range": [0, 1],
                    "description": "Side of the stage where the player is (0: Left, 1: Right)"
                },
                "wins": {
                    "type": "Box",
                    "value_range": [0, 2],
                    "description": "Number of rounds won by the player"
                },
                "character": {
                    "type": "Discrete",
                    "value_range": [0, 10],
                    "description": "Index of character in use (0: Kasumi, ..., 10: Ayane)"
                },
                "health": {
                    "type": "Box",
                    "value_range": [0, 208],
                    "description": "Health bar value"
                }
            }
        },
        "filter_keys": get_filter_keys("doapp", flatten=False)  # Dynamically added
    },
    "sfiii3n": {
        "game_id": "sfiii3n",
        "original_rom_name": "sfiii3n.zip",
        "sha256_checksum": "7239b5eb005488db22ace477501c574e9420c0ab70aeeb0795dfeb474284d416",
        "search_keywords": [
            "STREET FIGHTER III 3RD STRIKE: FIGHT FOR THE FUTUR [JAPAN] (CLONE)",
            "street-fighter-iii-3rd-strike-fight-for-the-futur-japan-clone",
            "106255",
            "wowroms"
        ],
        "resolution": (224, 384, 3),
        "moves": [
            "No-Move", "Left", "Left+Up", "Up", "Up+Right",
            "Right", "Right+Down", "Down", "Down+Left"
        ],
        "attacks": [
            "No-Attack", "Low Punch", "Medium Punch", "High Punch",
            "Low Kick", "Medium Kick", "High Kick",
            "Low Punch+Low Kick", "Medium Punch+Medium Kick", "High Punch+High Kick"
        ],
        "max_difficulty": 8,
        "num_characters": 20,
        "max_outfits": 7,
        "num_stages": 10,
        "game_type": game_type.get("sfiii3n", "unknown"),
        "characters": available_characters.get("sfiii3n", []),
        "action_spaces": {
            "discrete": 18,  # 9 moves + 10 attacks - 1 no-op double count
            "multi_discrete": 90  # 9 moves * 10 attacks
        },
        "observation_space": {
            "global": {
                "frame": {
                    "type": "Box",
                    "value_range": [0, 255],
                    "description": "Latest game frame (RGB pixel screen)"
                },
                "stage": {
                    "type": "Box",
                    "value_range": [1, 10],
                    "description": "Current stage of the game"
                },
                "timer": {
                    "type": "Box",
                    "value_range": [0, 100],
                    "description": "Round time remaining"
                }
            },
            "player_specific": {
                "side": {
                    "type": "Discrete (Binary)",
                    "value_range": [0, 1],
                    "description": "Side of the stage where the player is (0: Left, 1: Right)"
                },
                "wins": {
                    "type": "Box",
                    "value_range": [0, 2],
                    "description": "Number of rounds won by the player"
                },
                "character": {
                    "type": "Discrete",
                    "value_range": [0, 19],
                    "description": "Index of character in use (0: Alex, ..., 19: Gill)"
                },
                "health": {
                    "type": "Box",
                    "value_range": [-1, 160],
                    "description": "Health bar value"
                },
                "stun_bar": {
                    "type": "Box",
                    "value_range": [0, 72],
                    "description": "Stun bar value"
                },
                "stunned": {
                    "type": "Discrete (Binary)",
                    "value_range": [0, 1],
                    "description": "Stunned flag"
                },
                "super_bar": {
                    "type": "Box",
                    "value_range": [0, 128],
                    "description": "Super bar value"
                },
                "super_type": {
                    "type": "Discrete",
                    "value_range": [0, 2],
                    "description": "Selected type of super move (0-1-2: Super Type 1-2-3)"
                },
                "super_count": {
                    "type": "Box",
                    "value_range": [0, 3],
                    "description": "Count of activated super moves"
                },
                "super_max": {
                    "type": "Box",
                    "value_range": [1, 3],
                    "description": "Maximum number of activated super moves"
                }
            }
        },
        "filter_keys": get_filter_keys("sfiii3n", flatten=False)  # Dynamically added
    },
    "tektagt": {
        "game_id": "tektagt",
        "original_rom_name": "tektagt.zip",  # Renamed from tektagtac.zip
        "sha256_checksum": "57be777eae0ee9e1c035a64da4c0e7cb7112259ccebe64e7e97029ac7f01b168",
        "search_keywords": [
            "TEKKEN TAG TOURNAMENT [ASIA] (CLONE)",
            "tekken-tag-tournament-asia-clone",
            "108661",
            "wowroms"
        ],
        "resolution": (240, 512, 3),
        "moves": [
            "No-Move", "Left", "Left+Up", "Up", "Up+Right",
            "Right", "Right+Down", "Down", "Down+Left"
        ],
        "attacks": [
            "No-Attack", "Left Punch", "Right Punch", "Left Kick", "Right Kick", "Tag",
            "Left Punch+Right Punch", "Left Punch+Left Kick", "Left Punch+Right Kick",
            "Right Punch+Left Kick", "Right Punch+Right Kick", "Right Punch+Tag",
            "Left Kick+Right Kick"
        ],
        "max_difficulty": 9,
        "num_characters": 39,  # Including the "Unknown" character
        "max_outfits": 5,  # Some characters may have fewer outfits
        "num_stages": 8,
        "game_type": game_type.get("tektagt", "unknown"),
        "characters": available_characters.get("tektagt", []),
        "action_spaces": {
            "discrete": 21,  # 9 moves + 13 attacks - 1 no-op double count
            "multi_discrete": 117  # 9 moves * 13 attacks
        },
        "observation_space": {
            "global": {
                "frame": {
                    "type": "Box",
                    "value_range": [0, 255],
                    "description": "Latest game frame (RGB pixel screen)"
                },
                "stage": {
                    "type": "Box",
                    "value_range": [1, 8],
                    "description": "Current stage of the game"
                },
                "timer": {
                    "type": "Box",
                    "value_range": [0, 60],
                    "description": "Round time remaining"
                }
            },
            "player_specific": {
                "side": {
                    "type": "Discrete (Binary)",
                    "value_range": [0, 1],
                    "description": "Side of the stage where the player is (0: Left, 1: Right)"
                },
                "wins": {
                    "type": "Box",
                    "value_range": [0, 2],
                    "description": "Number of rounds won by the player"
                },
                "character_1": {
                    "type": "Discrete",
                    "value_range": [0, 38],
                    "description": "Index of first character slot"
                },
                "character_2": {
                    "type": "Discrete",
                    "value_range": [0, 38],
                    "description": "Index of second character slot"
                },
                "character": {
                    "type": "Discrete",
                    "value_range": [0, 38],
                    "description": "Index of character in use"
                },
                "health_1": {
                    "type": "Box",
                    "value_range": [0, 227],
                    "description": "Health bar value for first character in use"
                },
                "health_2": {
                    "type": "Box",
                    "value_range": [0, 227],
                    "description": "Health bar value for second character in use"
                },
                "active_character": {
                    "type": "Discrete (Binary)",
                    "value_range": [0, 1],
                    "description": "Index of the active character (0: first, 1: second)"
                },
                "bar_status": {
                    "type": "Discrete",
                    "value_range": [0, 4],
                    "description": (
                        "Status of the background character health bar: "
                        "0: reserve health bar almost filled, "
                        "1: small amount of health lost, recharging in progress, "
                        "2: large amount of health lost, recharging in progress, "
                        "3: rage mode on, combo attack ready, "
                        "4: no background character (final boss)"
                    )
                }
            }
        },
        "filter_keys": get_filter_keys("tektagt", flatten=False)  # Dynamically added
    },
    "umk3": {
        "game_id": "umk3",
        "original_rom_name": "umk3.zip",  # Renamed from umk3r10.zip
        "sha256_checksum": "f48216ad82f78cb86e9c07d2507be347f904f4b5ae354a85ae7c34d969d265af",
        "search_keywords": [
            "ULTIMATE MORTAL KOMBAT 3 (CLONE)",
            "ultimate-mortal-kombat-3-clone",
            "109574",
            "wowroms"
        ],
        "resolution": (254, 500, 3),
        "moves": [
            "No-Move", "Left", "Left+Up", "Up", "Up+Right",
            "Right", "Right+Down", "Down", "Down+Left"
        ],
        "attacks": [
            "No-Attack", "High Punch", "High Kick", "Low Kick",
            "Low Punch", "Run", "Block"
        ],
        "max_difficulty": 5,
        "num_characters": 26,  # Including hidden characters
        "max_outfits": 1,
        "num_stages": {
            "tower_1": 8,
            "tower_2": 9,
            "tower_3": 10,
            "tower_4": 11
        },
        "game_type": game_type.get("umk3", "unknown"),
        "characters": available_characters.get("umk3", []),
        "action_spaces": {
            "discrete": 15,  # 9 moves + 7 attacks - 1 no-op double count
            "multi_discrete": 63  # 9 moves * 7 attacks
        },
        "observation_space": {
            "global": {
                "frame": {
                    "type": "Box",
                    "value_range": [0, 255],
                    "description": "Latest game frame (RGB pixel screen)"
                },
                "stage": {
                    "type": "Box",
                    "value_range": [1, 11],
                    "description": "Current stage of the game"
                },
                "timer": {
                    "type": "Box",
                    "value_range": [0, 100],
                    "description": "Round time remaining"
                }
            },
            "player_specific": {
                "side": {
                    "type": "Discrete (Binary)",
                    "value_range": [0, 1],
                    "description": "Side of the stage where the player is (0: Left, 1: Right)"
                },
                "wins": {
                    "type": "Box",
                    "value_range": [0, 2],
                    "description": "Number of rounds won by the player"
                },
                "character": {
                    "type": "Discrete",
                    "value_range": [0, 25],
                    "description": (
                        "Index of character in use "
                        "(0: Kitana, 1: Reptile, ..., 25: Shao Kahn)"
                    )
                },
                "health": {
                    "type": "Box",
                    "value_range": [0, 166],
                    "description": "Health bar value"
                },
                "aggressor_bar": {
                    "type": "Box",
                    "value_range": [0, 48],
                    "description": "Aggressor bar value"
                }
            }
        },
        "filter_keys": get_filter_keys("umk3", flatten=False)  # Dynamically added
    },
    "samsh5sp": {
        "game_id": "samsh5sp",
        "original_rom_name": "samsh5sp.zip",
        "sha256_checksum": "adf33d8a02f3d900b4aa95e62fb21d9278fb920b179665b12a489bd39a6c103d",
        "search_keywords": [
            "SAMURAI SHODOWN V SPECIAL",
            "samurai-shodown-v-special",
            "100347",
            "wowroms"
        ],
        "resolution": (224, 320, 3),
        "moves": [
            "No-Move", "Left", "Left+Up", "Up", "Up+Right",
            "Right", "Right+Down", "Down", "Down+Left"
        ],
        "attacks": [
            "No-Attack", "Weak Slash", "Medium Slash", "Kick", "Meditation",
            "Weak Slash + Medium Slash (Strong Slash)",
            "Medium Slash + Kick (Surprise Attack)",
            "Weak Slash + Kick", "Kick + Meditation",
            "Weak Slash + Medium Slash + Kick (Rage)",
            "Medium Slash + Kick + Meditation"
        ],
        "max_difficulty": 8,
        "num_characters": 28,
        "max_outfits": 4,
        "num_stages": 7,
        "game_type": game_type.get("samsh5sp", "unknown"),
        "characters": available_characters.get("samsh5sp", []),
        "action_spaces": {
            "discrete": 19,  # 9 moves + 11 attacks - 1 no-op double count
            "multi_discrete": 99  # 9 moves * 11 attacks
        },
        "observation_space": {
            "global": {
                "frame": {
                    "type": "Box",
                    "value_range": [0, 255],
                    "description": "Latest game frame (RGB pixel screen)"
                },
                "stage": {
                    "type": "Box",
                    "value_range": [1, 7],
                    "description": "Current stage of the game"
                },
                "timer": {
                    "type": "Box",
                    "value_range": [0, 60],
                    "description": "Round time remaining"
                }
            },
            "player_specific": {
                "side": {
                    "type": "Discrete (Binary)",
                    "value_range": [0, 1],
                    "description": "Side of the stage where the player is (0: Left, 1: Right)"
                },
                "wins": {
                    "type": "Box",
                    "value_range": [0, 3],
                    "description": "Number of rounds won by the player"
                },
                "character": {
                    "type": "Discrete",
                    "value_range": [0, 27],
                    "description": (
                        "Index of character in use "
                        "(0: Kyoshiro, ..., 27: Mizuki)"
                    )
                },
                "health": {
                    "type": "Box",
                    "value_range": [0, 125],
                    "description": "Health bar value"
                },
                "rage_on": {
                    "type": "Discrete (Binary)",
                    "value_range": [0, 1],
                    "description": "Rage active for the player (0: False, 1: True)"
                },
                "rage_used": {
                    "type": "Discrete (Binary)",
                    "value_range": [0, 1],
                    "description": "Rage used (0: False, 1: True)"
                },
                "weapon_lost": {
                    "type": "Discrete (Binary)",
                    "value_range": [0, 1],
                    "description": "Weapon lost by the player (0: False, 1: True)"
                },
                "weapon_fight": {
                    "type": "Discrete (Binary)",
                    "value_range": [0, 1],
                    "description": "Weapon fight condition triggered (0: False, 1: True)"
                },
                "rage_bar": {
                    "type": "Box",
                    "value_range": [0, 100],
                    "description": "Rage bar value"
                },
                "weapon_bar": {
                    "type": "Box",
                    "value_range": [0, 120],
                    "description": "Weapon bar value"
                },
                "power_bar": {
                    "type": "Box",
                    "value_range": [0, 64],
                    "description": "Power bar value"
                }
            }
        },
        "filter_keys": get_filter_keys("samsh5sp", flatten=False)  # Dynamically added
    },
    "kof98umh": {
        "game_id": "kof98umh",
        "original_rom_name": "kof98umh.zip",
        "sha256_checksum": "beb7bdea87137832f5f6d731fd1abd0350c0cd6b6b2d57cab2bedbac24fe8d0a",
        "search_keywords": [
            "The King Of Fighters '98: Ultimate Match HERO",
            "kof98umh",
            "allmyroms"
        ],
        "resolution": (240, 320, 3),
        "moves": [
            "No-Move", "Left", "Left+Up", "Up", "Up+Right",
            "Right", "Right+Down", "Down", "Down+Left"
        ],
        "attacks": [
            "No-Attack", "Weak Punch", "Weak Kick", "Strong Punch",
            "Strong Kick", "Weak Punch + Weak Kick", 
            "Strong Punch + Strong Kick", 
            "Weak Punch + Weak Kick + Strong Punch + Strong Kick",
            "Weak Punch + Weak Kick + Strong Punch"
        ],
        "max_difficulty": 8,
        "num_characters": 45,  # Including hidden characters
        "max_outfits": 4,
        "num_stages": 7,
        "game_type": game_type.get("kof98umh", "unknown"),
        "characters": available_characters.get("kof98umh", []),
        "action_spaces": {
            "discrete": 17,  # 9 moves + 9 attacks - 1 no-op double count
            "multi_discrete": 81  # 9 moves * 9 attacks
        },
        "observation_space": {
            "global": {
                "frame": {
                    "type": "Box",
                    "value_range": [0, 255],
                    "description": "Latest game frame (RGB pixel screen)"
                },
                "stage": {
                    "type": "Box",
                    "value_range": [1, 7],
                    "description": "Current stage of the game"
                },
                "timer": {
                    "type": "Box",
                    "value_range": [0, 60],
                    "description": "Round time remaining"
                }
            },
            "player_specific": {
                "side": {
                    "type": "Discrete (Binary)",
                    "value_range": [0, 1],
                    "description": "Side of the stage where the player is (0: Left, 1: Right)"
                },
                "wins": {
                    "type": "Box",
                    "value_range": [0, 3],
                    "description": "Number of rounds won by the player"
                },
                "character_1": {
                    "type": "Discrete",
                    "value_range": [0, 44],
                    "description": "Index of first character slot"
                },
                "character_2": {
                    "type": "Discrete",
                    "value_range": [0, 44],
                    "description": "Index of second character slot"
                },
                "character_3": {
                    "type": "Discrete",
                    "value_range": [0, 44],
                    "description": "Index of third character slot"
                },
                "character": {
                    "type": "Discrete",
                    "value_range": [0, 44],
                    "description": "Index of character in use"
                },
                "health": {
                    "type": "Box",
                    "value_range": [-1, 119],
                    "description": "Health bar value"
                },
                "power_bar": {
                    "type": "Box",
                    "value_range": [0, 100],
                    "description": "Power bar value"
                },
                "special_attacks": {
                    "type": "Box",
                    "value_range": [0, 5],
                    "description": "Number of special attacks available"
                },
                "bar_type": {
                    "type": "Discrete",
                    "value_range": [0, 7],
                    "description": (
                        "Index of bar type: "
                        "0: Advanced / Ultimate (Dash Advanced, Evade Advanced, Bar Advanced), "
                        "1: Extra / Ultimate (Dash Extra, Evade Extra, Bar Extra), "
                        "2: Ultimate (Dash Extra, Evade Advanced, Bar Advanced), "
                        "3: Ultimate (Dash Advanced, Evade Advanced, Bar Extra), "
                        "4: Ultimate (Dash Extra, Evade Advanced, Bar Extra), "
                        "5: Ultimate (Dash Advanced, Evade Extra, Bar Advanced), "
                        "6: Ultimate (Dash Extra, Evade Extra, Bar Advanced), "
                        "7: Ultimate (Dash Advanced, Evade Extra, Bar Extra)"
                    )
                }
            }
        },
        "filter_keys": get_filter_keys("kof98umh", flatten=False)  # Dynamically added
    },
    "mvsc": {
        "game_id": "mvsc",
        "original_rom_name": "mvsc.zip",
        "sha256_checksum": "6f63627cc37c554f74e8bf07b21730fa7f85511c7d5d07449850be98dde91da8",
        "search_keywords": [
            "marvel vs capcom clash of super heroes",
            "marvel-vs.-capcom-clash-of-super-heroes-euro-980123",
            "5511",
            "wowroms"
        ],
        "resolution": (224, 384, 3),
        "moves": [
            "No-Move", "Left", "Left+Up", "Up", "Up+Right",
            "Right", "Right+Down", "Down", "Down+Left"
        ],
        "attacks": [
            "No-Attack", "Weak Punch", "Medium Punch", "Strong Punch", "Weak Kick", "Medium Kick", "Strong Kick",
            "WP+MP", "MP+SP", "WP+SP", "WK+MK", "MK+SK", "WK+SK",
            "WP+WK", "MP+MK", "SP+SK", "MP+WK", "WP+MP+SP", "WK+MK+SK"
        ],
        "max_difficulty": 8,
        "num_characters": 22,  # Including alternate characters
        "max_outfits": 2,
        "num_stages": 8,
        "game_type": game_type.get("mvsc", "unknown"),
        "characters": available_characters.get("mvsc", []),
        "action_spaces": {
            "discrete": 27,  # 9 moves + 19 attacks - 1 no-op double count
            "multi_discrete": 171  # 9 moves * 19 attacks
        },
        "observation_space": {
            "global": {
                "frame": {
                    "type": "Box",
                    "value_range": [0, 255],
                    "description": "Latest game frame (RGB pixel screen)"
                },
                "stage": {
                    "type": "Box",
                    "value_range": [1, 8],
                    "description": "Current stage of the game"
                },
                "timer": {
                    "type": "Box",
                    "value_range": [0, 99],
                    "description": "Round time remaining"
                }
            },
            "player_specific": {
                "side": {
                    "type": "Discrete (Binary)",
                    "value_range": [0, 1],
                    "description": "Side of the stage where the player is (0: Left, 1: Right)"
                },
                "wins": {
                    "type": "Box",
                    "value_range": [0, 1],
                    "description": "Number of rounds won by the player"
                },
                "character_1": {
                    "type": "Discrete",
                    "value_range": [0, 21],
                    "description": "Index of first character slot"
                },
                "character_2": {
                    "type": "Discrete",
                    "value_range": [0, 21],
                    "description": "Index of second character slot"
                },
                "character": {
                    "type": "Discrete",
                    "value_range": [0, 21],
                    "description": "Index of character in use"
                },
                "health_1": {
                    "type": "Box",
                    "value_range": [0, 144],
                    "description": "Health bar value for first character in use"
                },
                "health_2": {
                    "type": "Box",
                    "value_range": [0, 144],
                    "description": "Health bar value for second character in use"
                },
                "active_character": {
                    "type": "Discrete (Binary)",
                    "value_range": [0, 1],
                    "description": "Index of the active character (1: first, 0: second)"
                },
                "super_bar": {
                    "type": "Box",
                    "value_range": [0, 144],
                    "description": "Super bar value"
                },
                "super_count": {
                    "type": "Box",
                    "value_range": [0, 3],
                    "description": "Count of activated super moves"
                },
                "partner": {
                    "type": "Discrete",
                    "value_range": [0, 21],
                    "description": (
                        "Index of assist partner in use "
                        "(e.g., 0: Lou, 1: Juggernaut, ..., 21: Sentinel)"
                    )
                },
                "partner_attacks": {
                    "type": "Box",
                    "value_range": [0, 9],
                    "description": "Count of available partner attacks"
                }
            }
        },
        "filter_keys": get_filter_keys("mvsc", flatten=False)  # Dynamically added
    },
    "xmvsf": {
        "game_id": "xmvsf",
        "original_rom_name": "xmvsf.zip",
        "sha256_checksum": "833aa46af63a3ad87f69ce2bacd85a4445f35a50e3aff4f793f069b205b51c60",
        "search_keywords": [
            "x-men vs street fighter",
            "x-men-vs.-street-fighter-usa-961004",
            "8769",
            "wowroms"
        ],
        "resolution": (224, 384, 3),
        "moves": [
            "No-Move", "Left", "Left+Up", "Up", "Up+Right",
            "Right", "Right+Down", "Down", "Down+Left"
        ],
        "attacks": [
            "No-Attack", "Weak Punch", "Medium Punch", "Strong Punch", "Weak Kick", 
            "Medium Kick", "Strong Kick", "WP+MP", "MP+SP", "WP+SP", 
            "WK+MK", "MK+SK", "WK+SK", "WP+WK", "SP+SK", "MP+WK", 
            "WP+MP+SP", "WK+MK+SK"
        ],
        "max_difficulty": 8,
        "num_characters": 19,  # Including hidden characters
        "max_outfits": 2,
        "num_stages": 8,
        "game_type": game_type.get("xmvsf", "unknown"),
        "characters": available_characters.get("xmvsf", []),
        "action_spaces": {
            "discrete": 26,  # 9 moves + 18 attacks - 1 no-op double count
            "multi_discrete": 162  # 9 moves * 18 attacks
        },
        "observation_space": {
            "global": {
                "frame": {
                    "type": "Box",
                    "value_range": [0, 255],
                    "description": "Latest game frame (RGB pixel screen)"
                },
                "stage": {
                    "type": "Box",
                    "value_range": [1, 8],
                    "description": "Current stage of the game"
                },
                "timer": {
                    "type": "Box",
                    "value_range": [0, 99],
                    "description": "Round time remaining"
                }
            },
            "player_specific": {
                "side": {
                    "type": "Discrete (Binary)",
                    "value_range": [0, 1],
                    "description": "Side of the stage where the player is (0: Left, 1: Right)"
                },
                "wins": {
                    "type": "Box",
                    "value_range": [0, 1],
                    "description": "Number of rounds won by the player"
                },
                "character_1": {
                    "type": "Discrete",
                    "value_range": [0, 18],
                    "description": "Index of first character slot"
                },
                "character_2": {
                    "type": "Discrete",
                    "value_range": [0, 18],
                    "description": "Index of second character slot"
                },
                "character": {
                    "type": "Discrete",
                    "value_range": [0, 18],
                    "description": "Index of character in use"
                },
                "health_1": {
                    "type": "Box",
                    "value_range": [0, 144],
                    "description": "Health bar value for first character in use"
                },
                "health_2": {
                    "type": "Box",
                    "value_range": [0, 144],
                    "description": "Health bar value for second character in use"
                },
                "active_character": {
                    "type": "Discrete (Binary)",
                    "value_range": [0, 1],
                    "description": "Index of the active character (1: first, 0: second)"
                },
                "super_bar": {
                    "type": "Box",
                    "value_range": [0, 144],
                    "description": "Super bar value"
                },
                "super_count": {
                    "type": "Box",
                    "value_range": [0, 3],
                    "description": "Count of activated super moves"
                }
            }
        },
        "filter_keys": get_filter_keys("xmvsf", flatten=False)  # Dynamically added
    },
    "soulclbr": {
        "game_id": "soulclbr",
        "original_rom_name": "soulclbr.zip",
        "sha256_checksum": "a07a1a19995d582b56f2865783c5d7adb7acb9a6ad995a26fc7c4cfecd821817",
        "search_keywords": [
            "soul calibur",
            "soul-calibur",
            "106959",
            "wowroms"
        ],
        "resolution": (240, 512, 3),
        "moves": [
            "No-Move", "Left", "Left+Up", "Up", "Up+Right",
            "Right", "Right+Down", "Down", "Down+Left"
        ],
        "attacks": [
            "No-Attack", "Horizontal Attack", "Vertical Attack", "Kick", "Guard",
            "HA+VA", "HA+K", "VA+K", "HA+G", "VA+G", "K+G", 
            "HA+VA+K", "HA+VA+G"
        ],
        "max_difficulty": 5,
        "num_characters": 18,  # Including hidden characters
        "max_outfits": 2,
        "num_stages": 8,
        "game_type": game_type.get("soulclbr", "unknown"),
        "characters": available_characters.get("soulclbr", []),
        "action_spaces": {
            "discrete": 21,  # 9 moves + 13 attacks - 1 no-op double count
            "multi_discrete": 117  # 9 moves * 13 attacks
        },
        "observation_space": {
            "global": {
                "frame": {
                    "type": "Box",
                    "value_range": [0, 255],
                    "description": "Latest game frame (RGB pixel screen)"
                },
                "stage": {
                    "type": "Box",
                    "value_range": [1, 8],
                    "description": "Current stage of the game"
                },
                "timer": {
                    "type": "Box",
                    "value_range": [0, 40],
                    "description": "Round time remaining"
                }
            },
            "player_specific": {
                "side": {
                    "type": "Discrete (Binary)",
                    "value_range": [0, 1],
                    "description": "Side of the stage where the player is (0: Left, 1: Right)"
                },
                "wins": {
                    "type": "Box",
                    "value_range": [0, 2],
                    "description": "Number of rounds won by the player"
                },
                "character": {
                    "type": "Discrete",
                    "value_range": [0, 17],
                    "description": "Index of character in use"
                },
                "health": {
                    "type": "Box",
                    "value_range": [0, 240],
                    "description": "Health bar value"
                }
            }
        },
        "filter_keys": get_filter_keys("soulclbr", flatten=False)  # Dynamically added
    }
}

# Utility function to retrieve game-specific info
def get_game_info(game_id):
    return game_info.get(game_id, {})
