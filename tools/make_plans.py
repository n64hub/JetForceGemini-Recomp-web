#!/usr/bin/env python3
"""Writes tools/shader_plan.json, tools/play_plan.json and tools/play_plan_extended.json, the plans N64Recomp-browser's
tools/record_shaders.mjs and play_page.mjs follow for the web page (src/rt64_shaders.txt's header says how the list was recorded with the first).
Both reach the game the same way: the save deleted, so that Game 1 is a new game on every load, then the launcher's
Start Game, the logos and the title, Start to the file select, A on New Game and on the name keyboard's 1, the stick
down to END and A, the story intro skipped with Start, and the character select. From there a section picks Juno,
whose opening is Goldwood's, and tools/shader_survey.js warps to each room of a planet by the game's level numbers
(a warp straight from the character select leaves the screen black); in each the camera turns (the C buttons, the
arrow keys) and the character walks (W) for a few seconds. A section a planet: every room of the planet's regions (the
region is byte 0x102 of a level's header, src/jfg/jfg_debug_menu.cpp's region_names), the cutscenes and test rooms
that belong to none left out. Places that draw shaders a planet's rooms don't (FIGHTS: bosses, a cutscene, a race) are
played again in a load of their own under their planet's section name, every weapon given (shader_survey.js's arm()),
enemies fought for about 25 s a round: out and back by as much, firing as it goes (Z), aiming (R), the camera turned,
jumping and changing weapon. The play plan, the page's regular play, plays Goldwood's first room, one FIGHT round, its
boot's timeouts cut to what a run needs so that it takes at most 3 minutes with every one run out; the extended plan,
for when a longer play is needed, plays every room in PLAYS that way, at most 5 minutes. Run it again after changing
PLANETS, FIGHTS or PLAYS."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))

# A section a planet, in the order the game reaches them: its rooms, the first where a player lands, and the character
# who plays there first, by the game's numbers.
VELA, JUNO, LUPUS = 0, 1, 2
PLANETS = [
    ("goldwood", JUNO, [21, 16, 26, 288, 289, 25, 106, 126, 169, 211, 215, 218, 219, 290, 291, 27, 54, 85, 236,
                        24, 87, 95, 227, 228, 310]),
    ("anubis", JUNO, [37, 39, 40, 84, 129, 130, 131, 134, 241, 38, 123, 124, 128, 154, 297, 86, 152, 156]),
    ("tawfret", JUNO, [158, 115, 118, 231, 242, 244, 247, 255, 256, 257, 121, 125, 132, 133, 147, 149, 150, 217, 259,
                       260, 261, 136, 138, 254, 318, 194, 195]),
    ("walkway", JUNO, [22, 6, 12, 13, 34]),
    ("sekhmet", JUNO, [67, 4, 5, 7, 8, 10, 11, 50, 51, 52]),
    ("rithessa", JUNO, [29, 65, 80, 81, 167, 30, 31, 56, 112, 32, 82, 179, 182, 186, 196, 208, 209]),
    ("cerulean", VELA, [53, 2, 14, 113, 114, 265, 266, 298]),
    ("ichor", VELA, [43, 18, 19, 41, 42, 44, 119, 139, 49, 143, 187, 262, 339, 375]),
    ("spawnship", VELA, [3, 55, 57, 58, 59, 60, 61, 62, 63, 64]),
    ("waterruin", LUPUS, [229, 246]),
    ("gemquarry", LUPUS, [272, 267, 36, 294, 295, 403]),
    ("eschebone", JUNO, [216, 198, 183, 184, 188, 191, 120, 142, 148, 189, 190, 203, 204, 205, 249, 206, 214]),
    ("spacestation", JUNO, [276, 9, 104, 264]),
    ("mizar", JUNO, [232, 192, 201, 213, 299, 300, 301, 222, 223, 234, 311, 243, 315, 316, 317]),
    ("asteroid", JUNO, [332, 28, 220, 224, 225, 226, 337, 396]),
]

# Places further in, by the game's level numbers, where a longer play draws shaders the rooms above don't: (section,
# [(level, character, seconds waited after the warp, rounds of FIGHT)]), each section's in one load, in this order.
FIGHTS = [
    ("tawfret", [(193, JUNO, 12, 0), (194, JUNO, 5, 2)]),  # Swamp Boss Intro, then its fight (Tawfret - Castle)
    ("sekhmet", [(162, JUNO, 6, 1)]),  # AlphaSewer Boss, the battle cruiser's
    ("ichor", [(371, VELA, 10, 0), (372, VELA, 5, 2)]),  # SlugBoss Play Sequence, then its fight (Military Base)
    ("spawnship", [(326, JUNO, 12, 0)]),  # Spawn Attack, a cutscene of no planet's, on into Control Room (323)
    ("mizar", [(268, JUNO, 5, 1)]),  # Mizar Racer, the race against Mizar
    ("asteroid", [(386, JUNO, 5, 2)]),  # Mizar Fight Play
]

def key(name, code, ms):
    return ["hold", name, name if len(name) > 1 else name.lower(), code, ms]

LOOK = [key("ArrowLeft", 37, 1500), ["hold", "KeyW", "w", 87, 1500], key("ArrowRight", 39, 1500), ["wait", 1000]]

# The game's own time for the play's waits and holds, and where the player is at its end.
CLOCK = ["clock", "n64r(0x800FD748)", 60]
WHERE = ["eval", "(() => { const f = (a) => new Float32Array(new Uint32Array([n64r(a)]).buffer)[0]; const o = n64r(n64r(0x800F2D0C)); "
                 "return [0x0C, 0x10, 0x14].map((i) => Math.round(f(o + i))); })()"]

def visit(level, character):
    return [["eval", f"warp({level}, {character})"], ["wait", 3500], *LOOK]

LOAD = [["until", "Device Name", 30000], ["wait", 9000]]
TITLE, STORY_FIRST, CHARACTER_SELECT, GOLDWOOD_OPENING = 349, 322, 127, 93
# Esc first: a fresh profile opens on the first-run language question (src/ui/ui_language_prompt.cpp), which Esc
# closes in English; with none open it only puts the launcher's focus on Play.
SETUP = [["key", "Escape", "Escape", 27], ["wait", 1000], ["rom", 473, 197], ["wait", 4000]]
# Load ROM once the shader list Chrome builds behind the launcher is done: a click while it builds can be lost. Firefox
# builds none there, and its line saying so is the one waited for. It is load's first step: an until takes only lines
# that come after it starts, and Firefox's line comes right after Device Name.
PLAY_LOAD = [["until", r"RT64: all \d+ prebuilt shaders built|once the game draws", 60000], ["wait", 5000]]
# A press of the stick: one row of the name keyboard.
DOWN = [["hold", "KeyS", "s", 83, 150], ["wait", 400]]
# The regular plan's: the list's line waited for less, as the regular play's 3 minutes need (Chrome's came in 17-55 s).
REGULAR_LOAD = [PLAY_LOAD[0][:2] + [40000], PLAY_LOAD[1]]
# The first step also turns the N64's controls on (src/jfg/jfg_web.cpp), which the keys below are: a new player's Modern
# profile plays with the mouse's buttons.
START = [["eval", "try { FS.unlink('/home/web_user/saves/jfg-us.bin'); } catch (e) {} "
                  "if (Module._jfg_web_n64_controls) Module._jfg_web_n64_controls();"],
         ["click", 765, 277], ["until", "Initialized RDRAM", 60000], ["wait", 3000],
         ["evalFile", "shader_survey.js"], ["eval", f"waitLevel({TITLE}, 60000)"],
         ["pressUntil", "Enter", "Enter", 13, 100, 1500, f"level() !== {TITLE}", 30000], ["wait", 2500],
         ["key", "Space", " ", 32], ["wait", 2000], ["key", "Space", " ", 32], ["wait", 1000],
         *DOWN * 4, ["key", "Space", " ", 32], ["eval", f"waitLevel({STORY_FIRST}, 15000)"],
         ["pressUntil", "Enter", "Enter", 13, 100, 1500, f"level() === {CHARACTER_SELECT}", 60000], ["wait", 3000]]
# Juno picked at the character select, into Goldwood's opening; kept only in Goldwood's section.
ENTER = [["pressUntil", "Space", " ", 32, 100, 1500, f"level() !== {CHARACTER_SELECT}", 30000],
         ["eval", f"waitLevel({GOLDWOOD_OPENING}, 15000)"], ["wait", 1500]]
# The play plan's START and ENTER: the same steps, each timeout what a run needs with room to spare (the title came
# 15-17 s after the save's evalFile, every other step in 5 s or less).
PLAY_START = [*START[:2], ["until", "Initialized RDRAM", 10000], ["wait", 2000], START[4],
              ["eval", f"waitLevel({TITLE}, 22000)"],
              ["pressUntil", "Enter", "Enter", 13, 100, 1500, f"level() !== {TITLE}", 10000], *START[7:-3],
              ["eval", f"waitLevel({STORY_FIRST}, 8000)"],
              ["pressUntil", "Enter", "Enter", 13, 100, 1500, f"level() === {CHARACTER_SELECT}", 10000], ["wait", 2000]]
PLAY_ENTER = [["pressUntil", "Space", " ", 32, 100, 1500, f"level() !== {CHARACTER_SELECT}", 8000],
              ["eval", f"waitLevel({GOLDWOOD_OPENING}, 12000)"], ["wait", 1500]]

def section_steps(name, character, rooms):
    enter = ENTER if name == "goldwood" else [["keep", False], *ENTER, ["keep", True]]
    return enter + [s for level in rooms for s in visit(level, character)]

KEY_W, KEY_A, KEY_S, KEY_D = ("KeyW", "w", 87), ("KeyA", "a", 65), ("KeyS", "s", 83), ("KeyD", "d", 68)
KEY_Z, KEY_R, KEY_A_BUTTON = ("KeyQ", "q", 81), ("KeyR", "r", 82), ("Space", " ", 32)
LEFT, RIGHT = ("ArrowLeft", "ArrowLeft", 37), ("ArrowRight", "ArrowRight", 39)
C_UP, C_DOWN = ("ArrowUp", "ArrowUp", 38), ("ArrowDown", "ArrowDown", 40)

def hold(k, ms):
    return ["hold", *k, ms]

def held(k, *steps):
    return [["down", *k], *steps, ["up", *k]]

def fire(ms):  # Z pressed every 300 ms for ms
    return ["pressUntil", *KEY_Z, 120, 300, "false", ms]

# A round about a spot: out and back by as much, firing as it goes, the camera turned, a jump, aiming. The play plan's
# rounds take a shot a second into aiming (the weapon's reticle: upstream's 511e603 keeps it drawn with Display Frame
# Rate, which every page has on).
def fight(aim_shot=None):
    aim = [fire(1000), ["shot", aim_shot], fire(1000)] if aim_shot else [fire(2000)]
    return [*held(KEY_W, fire(1800)), hold(KEY_A_BUTTON, 150), ["wait", 600],
         hold(LEFT, 900), *held(KEY_R, *aim), hold(RIGHT, 900),
         *held(KEY_S, fire(1800)), hold(C_UP, 200), ["wait", 800], hold(KEY_A_BUTTON, 150), ["wait", 600],
         *held(KEY_D, fire(1500)), *held(KEY_A, fire(1500)),
         hold(RIGHT, 900), fire(2500), hold(LEFT, 900), hold(C_DOWN, 300), ["wait", 500],
         hold(KEY_A_BUTTON, 150), ["wait", 600], fire(2500)]

FIGHT = fight()

def fight_steps(places):
    steps = [["keep", False], *ENTER, ["eval", "arm()"], ["keep", True]]
    for level, character, wait, rounds in places:
        steps += [["eval", f"warp({level}, {character})"], ["wait", wait * 1000], ["eval", "arm()"], *FIGHT * rounds]
    return steps

# The play plan's rooms, by the game's level numbers: (name, level, character, seconds), Goldwood's first room (the first
# a player lands in) and three of other looks. Each is a need that fails the run unless that level is playing within
# the seconds given (Goldwood's 12: in Firefox the game waits about 10 s there for Goldwood's section, which its opening
# starts), every weapon and the invulnerability cheat given (arm()), a shot about 8 s in and a FIGHT round, about 30 s.
PLAYS = [("goldwood", 21, JUNO, 12), ("tawfret-castle", 136, JUNO, 5), ("ichor", 49, VELA, 5),
         ("water-ruin", 246, LUPUS, 5)]

def play_steps(name, level, character, seconds, regular=False):
    return [["need", f"warp({level}, {character}, 0, {seconds * 1000})"], ["wait", 3000], ["eval", "arm()"],
            *([] if regular else [["wait", 3000]]), ["shot", f"{name}.png"], *fight(f"{name}-aim.png")]

def sections():
    fights = dict(FIGHTS)
    for name, character, rooms in PLANETS:
        yield {"name": name, "steps": section_steps(name, character, rooms)}
        if name in fights:
            yield {"name": name, "steps": fight_steps(fights[name])}

shader_plan = {
    # The list's header (record_shaders.mjs writes it at the top of src/rt64_shaders.txt).
    "header": [
        "The RT64 shaders the web page builds: one shader description a line, other mode L and H, color combiner L and H,",
        "flags, in hex. RT64 specializes each one's WGSL when the page is built. The list is in sections (N64Recomp-browser's",
        "README, \"Give RT64 a list of the game's shaders\"): the lines above the first \"section\" line are the boot, built",
        "before the game starts, and each section after it is built when the game first draws with 4 of its shaders, the game",
        "waiting for it in Firefox (Chrome builds the whole list behind the game, a section at a time). One missing here is",
        "built behind the game when it is first drawn, and the page remembers it for the next visit.",
        "",
        "Recorded by tools/shader_plan.json (written by tools/make_plans.py, whose docstring says how it plays) with",
        "N64Recomp-browser's tools/record_shaders.mjs, from the page opened with ?record-shaders at its default settings,",
        "each section from a fresh load of the page: the boot is the launcher, the logos, the title, the file select, the",
        "name keyboard, the story intro and the character select; each section after it is one planet, every room of its",
        "regions reached by tools/shader_survey.js (make_plans.py lists them), the camera turned and the character walked",
        "a few steps in each, Goldwood's with its opening; and, in a load of their own, the places further in that draw",
        "shaders a planet's rooms don't: Tawfret's swamp boss, Sekhmet's boss, Ichor's slug boss, the race against Mizar in",
        "Mizar's Palace's and the fight with Mizar in Asteroid's, every weapon given and enemies fought for 25-50 s, and the",
        "Spawn Attack cutscene in Spawnship's. Not played: the other bosses and cutscenes, the other minigames, multiplayer",
        "and the other rooms that belong to no planet."],
    "page": "JetForceGeminiRecompiled.html",
    "load": LOAD, "setup": SETUP, "start": START,
    "sections": list(sections()),
}
play_plan = {
    "header": [
        "Jet Force Gemini's play plan for N64Recomp-browser's tools/play_page.mjs, written by tools/make_plans.py, its",
        "regular play of 2-3 minutes: the boot as the shader plan's (Load ROM once the shader list Chrome builds behind the",
        "launcher is done; Firefox builds none there, and its line saying so is the one waited for) and Goldwood's opening",
        "as Juno, then, in the same load, Goldwood's first room as Juno, about 25 s, reached by tools/shader_survey.js's",
        "warp(), a need that fails the run unless that level is the one playing: every weapon and the invulnerability cheat",
        "given (arm()), out and back by as much about where the warp leaves her, firing, aiming, jumping, turning the camera",
        "and changing weapon. Its waits and holds are on the game's own clock, Time (the 60ths it adds each frame's length",
        "to), so every browser plays as much of the room whatever frames it gives the game; the last step reads where the",
        "character is (the player list's first object). tools/play_plan_extended.json goes on to three more rooms, for",
        "when a longer play is needed."],
    "page": "JetForceGeminiRecompiled.html",
    "load": REGULAR_LOAD, "setup": SETUP, "start": PLAY_START,
    "play": PLAY_ENTER + [CLOCK, *play_steps(*PLAYS[0], regular=True), WHERE],
}
extended_plan = {
    "header": [
        "Jet Force Gemini's extended play plan for N64Recomp-browser's tools/play_page.mjs, written by tools/make_plans.py,",
        "at most 5 minutes, for when a longer play than the regular one (tools/play_plan.json) is needed: the boot as the",
        "shader plan's (Load ROM once the shader list Chrome builds behind the launcher is done; Firefox builds none there,",
        "and its line saying so is the one waited for) and Goldwood's opening as Juno, then, in the same load, four rooms",
        "played about 30 s each: Goldwood's first as Juno, Tawfret's castle as Juno, Ichor as Vela and the Water Ruin's lost",
        "island as Lupus, every weapon and the invulnerability cheat given (tools/shader_survey.js's arm()), out and back by",
        "as much about where the warp leaves the character, firing, aiming, jumping, turning the camera and changing weapon.",
        "Every room is reached by the survey's warp(), a need that fails the run unless that level is the one playing. Its",
        "waits and holds are on the game's own clock, Time (the 60ths it adds each frame's length to), so every browser",
        "plays as much of each room whatever frames it gives the game; the last step reads where the character is (the",
        "player list's first object)."],
    "page": "JetForceGeminiRecompiled.html",
    "load": PLAY_LOAD, "setup": SETUP, "start": PLAY_START,
    "play": PLAY_ENTER + [CLOCK, *[s for play in PLAYS for s in play_steps(*play)], WHERE],
}
for name, plan in (("shader_plan.json", shader_plan), ("play_plan.json", play_plan),
                   ("play_plan_extended.json", extended_plan)):
    with open(os.path.join(HERE, name), "w", newline="\n") as f:
        json.dump(plan, f, indent=1)
        f.write("\n")
