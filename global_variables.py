
class GlobalConfig:
    CTC: int = 40
    BET_MULTIPLIER: int = 2
    ANTE: int = 5
    BATCH_SIZE: int = 1_00 #bilo 1000
    PARALLEL_COMPUTING: bool = False #bilo True
    PRIZE_FIRST: bool = False
    CREATE_OUTCOMES: bool = False
    DRAWGAME_LIST: list = []
    OUTCOMES_DICT: dict = {0: [],}
    MACHINE_BUILD: bool = False

    #dodato da bi radio fg kako treba, povecava se u fg.logic
    FREE_GAMES_PLAYED = 0

    # GAME SPECIFIC GV
    REEL_HEIGHT: int = 3
    NUM_OF_REELS: int = 5
    
    #SIDE MULITPLIERS FOR FORTUNE FURY LRS
    MULTIPLIERS_ON = True
    LRS_MULTIPLIERS = [1,2,3,4,5]

    #SIDE COIN COUNTERS
    # COUNTER_ON = False
    # LRS_COUNTERS = [1,2,3]
    
    #JACKPOT PIPS ON TOP COUNTERS
    JACKPOT_PIPS_ON = False
    JACKPOT_PIPS_COUNTERS = [0,0,0,0,0]
    
    #DIMMERS ON FOR LOCKED ROWS
    DIMMERS_ON = True
    DIMMED_REELS = [0,1,2,3,4,5,6,7,8]  #List of row indices to dim

    #HOLD AND SPIN BONUS
    HNS_ROWS = 12
    HNS_COLS = 5

    # EXECUTION LIST
    EXECUTION_LIST = []

    # DASHBOARD
    meters = {}
    my_scenes = {}
    idle_playmode = {}
    my_logic = {}
    currently_played_cheat_id = 0

    # SEED
    RANDOM_SEED = 0

    # SYMBOLS
    SYMBOLS = []
    ETS, STE = {}, {}

    #ALWAYS_RELOAD_EXCEL = False
    ALWAYS_RELOAD_EXCEL = True

    WAYS = False

    POTS_BG = 1
    POTS_BG_SYMS = {0:["_COI_1_"]} #key: index of pot, value: list of symbols corresponding to pot

    POTS_FG = 1
    POTS_FG_SYMS = {0:["_COI_1_"]} #key: index of pot, value: list of symbols corresponding to pot

    PROG_JACKPOT_ETN = {1:"GRAND",2:"MAJOR",3:"MINOR",4:"MINI"} #ENUM TO NAME
    PROG_JACKPOT_ETV = {1:1000000,2:50000,3:2500,4:1000}#

class BonusNames:
    BASEGAME = "Base Game"
    FREEGAME = "Free Games"
    HOLDANDSPIN = "Hold 'n Spin"
    DRAWGAME = "Draw Game"
    PLAYERDECISION = "Player Decision"
    PICKAPRIZE = "Pick a Prize"
    WHEEL = "Wheel"
    PLAYERDECISION = "Player Decision"
    FREEGAME_RE_TRIG = "Free Games Re-Trigger"

class GroupConstants:
    REELS_BACK =        1
    SPINNING_SYMBOLS =  3
    REEL_SYMBOLS =      3
    SPINNING_LABELS =   4
    FRAMES =            4
    TOP_SCREEN =        5
    REELS_FRONT =       6
    REEL_LABELS =       7
    DASHBOARD_BLOCKER = 8
