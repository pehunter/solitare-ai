from game import Card, Game
from colorama import Fore
from player import chooseMove
import pprint
import json
import random

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

def main():
    demo = {
        "tableau": [
            [{"suit": 1, "value": 1}], 
            [{"hidden": True}, {"suit": 3, "value": 1}],
            [{"hidden": True}, {"hidden": True}, {"suit": 0, "value": 4}],
            [{"hidden": True}, {"hidden": True}, {"hidden": True}, {"suit": 0, "value": 11}],
            [{"hidden": True}, {"hidden": True}, {"hidden": True}, {"hidden": True}, {"suit": 0, "value": 2}],
            [{"hidden": True}, {"hidden": True}, {"hidden": True}, {"hidden": True}, {"hidden": True}, {"suit": 1, "value": 8}],
            [{"hidden": True}, {"hidden": True}, {"hidden": True}, {"hidden": True}, {"hidden": True}, {"hidden": True}, {"suit": 2, "value": 7}]
        ],
        "foundation": {
            "hearts": {"suit": 0, "value": 0}, 
            "spades": {"suit": 1, "value": 1}, 
            "diamonds": {"suit": 2, "value": 0}, 
            "clubs": {"suit": 3, "value": 0}
        },
        "draw": True, 
        "pile": {"suit": 3, "value": 10}
    }

    game = Game()
    turns = 0
    while not game.win():
        # game.printGame()
        state = json.loads(game.json())
        moves = findAllMoves(state)
        
        # print(moves)

        if(len(moves) == 0):
            print(Fore.YELLOW + "No moves left..?" + Fore.RESET)
            game.printGame()
            break

        # input()

        move = moves[random.randint(0,len(moves) - 1)]
        converted = [move['cmd']]
        match converted[0]:
            case 'tt':
                converted.extend([move['frm'], move['to'], move['ct']])
            case 'ft':
                continue
                converted.extend([move['suit'], move['to']])
            case 'tc':
                converted.extend([move['to']])
            case 'pt':
                converted.extend([move['to']])
            case _:
                pass
        
        # print(Fore.GREEN + f"Selected {converted}" + Fore.RESET)
        
        if not chooseMove(converted, game):
            print(Fore.RED + "Shouldn't happen???" + Fore.RESET)
            game.printGame()
            break

        turns = turns + 1
        if turns % 1000 == 0:
            game.printGame()
        if turns >= 10000:
            print("Restarting..")
            game = Game()
            turns = 0

    if game.win():
        game.printGame()
        print(Fore.CYAN + "Not it fucking winning..." + Fore.RESET)
        
if __name__ == "__main__":
    main()