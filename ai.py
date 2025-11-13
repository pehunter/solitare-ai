from game import Card, Game
from colorama import Fore
# from player import chooseMove
import pprint
import json
import random
import pandas as pd
import numpy as np

#Get all free cards (cards that can be appended to)
def getFree(data: dict) -> list[Card | bool]:
    #If freeCards is != 7 then there is a free space...
    freeCards = []
    for col in data["tableau"]:
        if len(col) > 0:
            freeCards.append(Card(col[-1]['suit'], col[-1]['value']))
        else:
            freeCards.append(True)
    return freeCards

#Gets possible locations to place card
def getMoves(card: Card, freeCards: list[Card | bool]) -> list[int]:
    moves = []
    for t, freeCard in enumerate(freeCards):
        isCard = isinstance(freeCard, Card)
        #Kings
        if (not isCard and card.value == 12) or (isCard and freeCard.tryAdd(card)):
            moves.append(t)
    return moves

#Returns a list of possible moves to make
def findAllMoves(data: dict):
    #Create foundation
    foundation = {
        0: Card(data["foundation"]["hearts"]["suit"], data["foundation"]["hearts"]["value"]),
        1: Card(data["foundation"]["spades"]["suit"], data["foundation"]["spades"]["value"]),
        2: Card(data["foundation"]["diamonds"]["suit"], data["foundation"]["diamonds"]["value"]),
        3: Card(data["foundation"]["clubs"]["suit"], data["foundation"]["clubs"]["value"])
    }

    pile = None
    if(data["pile"] != False):
        pile = Card(data["pile"]["suit"], data["pile"]["value"])

    #Get free cards
    freeCards = getFree(data)
    moveList = []
    
    for c in range(0,7):
        for idx, cardData in enumerate(data["tableau"][c]):
            #Skip hidden
            if "hidden" in cardData:
                continue

            #Get the card's count position (from player perspective) from its index
            ct = len(data["tableau"][c]) - idx
            card = Card(cardData["suit"], cardData["value"])
            # "tt" moves
            moves = getMoves(card, freeCards)
            for move in moves:
                moveList.append({
                    "cmd": "tt",
                    "frm": c + 1,
                    "to": move + 1,
                    "ct": ct
                })
        if len(data["tableau"][c]) > 0:
            lc = Card(data["tableau"][c][-1]["suit"], data["tableau"][c][-1]["value"])
            # "ft" moves
            for suit in range(0, 4):
                if(lc.tryAdd(foundation[suit])):
                    moveList.append({
                        "cmd": "ft",
                        "suit": suit + 1,
                        "to": c + 1
                    })

            # "tc" moves
            if foundation[lc.suit].tryNext(lc):
                moveList.append({
                    "cmd": "tc",
                    "to": c + 1
                })
            
            # "pt" moves
            if pile != None and lc.tryAdd(pile):
                moveList.append({
                    "cmd": "pt",
                    "to": c + 1
                })
    
    # "pc" moves
    if pile != None and foundation[pile.suit].tryNext(pile):
        moveList.append({
            "cmd": "pc"
        })
    
    # "d" moves
    if data["draw"] or pile != None:
        moveList.append({
            "cmd": "d"
        })

    return moveList


#Get the card's index in a 48 equation
def get48Idx(card: Card):
    return card.suit*12 + (card.value - 1)

def get48Title(index: int):
    suit = int(index/12)
    match suit:
        case 0: suit = 'H'
        case 1: suit = 'S'
        case 2: suit = 'D'
        case 3: suit = 'C'
    
    value = (index % 12) + 1
    match value:
        case 1: value = 'A'
        case 10: value = 'J'
        case 11: value = 'Q'
        case 12: value = 'K'
        case _: value = value
    return f"{suit}{value}"
#Get the card's "name"
# def getName(card: Card):
    # st = ""
    # match card.suit:
        # case 0: st = "H"
    # return f"{card.suit}"

#Generate the columns for Pandas DF
def genCols():
    #Generate columns
    cols = []
    for c in range(0, 48):
        t = get48Title(c)
        cols.append(f"Bottom_{t}")
        cols.append(f"Top_{t}")
        cols.append(f"Move_{t}")
        cols.append(f"Collect_{t}")
        cols.append(f"Foundation_{t}")
        cols.append(f"Pile_{t}")
    cols.append("Empty")
    cols.append("Draw")
    cols.append("Cmd")
    return cols

#Extract data from game state.
#Data is:
# 1. All end cards at bottom of stack (48) ✔️
# 2. All cards at top of stack (48) ✔️
# 3. All movable cards (48) ✔️
# 4. Collected cards (48) ✔️
# 5. Top of foundation (48) ✔️
# 6. Top of pile (48) ✔️
# 7. Cards in draw? (1) ✔️
# 8. Empty space available? (1) ✔️
# 9. All discovered cards (A NUMBER)
def extract(data: dict) -> pd.DataFrame:
    cardData = np.zeros((48, 6), dtype=np.int8)
    empty = False
    draw = False

    #Is this even needed?
    hidden = 0

    for col in data["tableau"]:
        if len(col) > 0:
            #Set bottom card
            bottom = Card(col[-1]["suit"], col[-1]["value"])
            cardData[get48Idx(bottom)][0] = 1

            #Set top card
            x = 0
            while "hidden" in col[x]:
                hidden = hidden + 1
                x = x + 1
            top = Card(col[x]["suit"], col[x]["value"])
            cardData[get48Idx(top)][1] = 1
            #Get middle cards
            while x < len(col):
                middle = Card(col[x]["suit"], col[x]["value"])
                cardData[get48Idx(middle)][2] = 1
                x = x + 1
        else:
            empty = True
    
    for suit in data["foundation"]:
        val = data["foundation"][suit]["value"]
        for z in range(1, val + 1):
            card = Card(data["foundation"][suit]["suit"], z)
            cardData[get48Idx(card)][3] = 1
        if(val > 0):
            card = Card(data["foundation"][suit]["suit"], val)
            cardData[get48Idx(card)][4] = 1

    if(data["pile"] != False):
        pile = Card(data["pile"]["suit"], data["pile"]["value"])
        cardData[get48Idx(pile)][5] = 1
    
    if(data["draw"]):
        draw = True
    # print(cardData)
    # print(f"Hidden: {hidden}")
    # print(f"Empty: {empty}")
    # print(f"Draw: {draw}")


    cols = genCols()
    shaped = np.append(cardData, [empty, draw, 9])
    shaped = np.reshape(shaped, (1, 48*6 + 3))
    df = pd.DataFrame(shaped, columns=cols)
    
    return df

def numCmd(cmd: str):
    match cmd:
        case 'tt': return 0
        case 'tc': return 1
        case 'd': return 2
        case 'pt': return 3
        case 'pc': return 4
        case 'ft': return 5
        case _: return "Yeah shouldn't happen"

# def main():
#     demo = {
#         "tableau": [
#             [{"suit": 1, "value": 1}], 
#             [{"hidden": True}, {"suit": 3, "value": 1}],
#             [{"hidden": True}, {"hidden": True}, {"suit": 0, "value": 4}],
#             [{"hidden": True}, {"hidden": True}, {"hidden": True}, {"suit": 0, "value": 11}],
#             [{"hidden": True}, {"hidden": True}, {"hidden": True}, {"hidden": True}, {"suit": 0, "value": 2}],
#             [{"hidden": True}, {"hidden": True}, {"hidden": True}, {"hidden": True}, {"hidden": True}, {"suit": 1, "value": 8}],
#             [{"hidden": True}, {"hidden": True}, {"hidden": True}, {"hidden": True}, {"hidden": True}, {"hidden": True}, {"suit": 2, "value": 7}]
#         ],
#         "foundation": {
#             "hearts": {"suit": 0, "value": 0}, 
#             "spades": {"suit": 1, "value": 1}, 
#             "diamonds": {"suit": 2, "value": 0}, 
#             "clubs": {"suit": 3, "value": 0}
#         },
#         "draw": True, 
#         "pile": {"suit": 3, "value": 10}
#     }

#     game = Game()
#     turns = 0
#     while not game.win():
#         game.printGame()
#         state = json.loads(game.json())
#         extract(state)
#         moves = findAllMoves(state)
        
#         # print(moves)

#         if(len(moves) == 0):
#             print(Fore.YELLOW + "No moves left..?" + Fore.RESET)
#             game.printGame()
#             break

#         input()

#         move = moves[random.randint(0,len(moves) - 1)]
#         converted = [move['cmd']]
#         match converted[0]:
#             case 'tt':
#                 converted.extend([move['frm'], move['to'], move['ct']])
#             case 'ft':
#                 continue
#                 converted.extend([move['suit'], move['to']])
#             case 'tc':
#                 converted.extend([move['to']])
#             case 'pt':
#                 converted.extend([move['to']])
#             case _:
#                 pass
        
#         print(Fore.GREEN + f"Selected {converted}" + Fore.RESET)
        
#         if not chooseMove(converted, game):
#             print(Fore.RED + "Shouldn't happen???" + Fore.RESET)
#             game.printGame()
#             break

#         turns = turns + 1
#         if turns % 1000 == 0:
#             game.printGame()
#         if turns >= 10000:
#             print("Restarting..")
#             game = Game()
#             turns = 0

#     if game.win():
#         game.printGame()
#         print(Fore.CYAN + "Not it fucking winning..." + Fore.RESET)
        
# if __name__ == "__main__":
#     main()