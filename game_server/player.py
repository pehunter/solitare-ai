### player.py
### Handles move deciphering and controls the game.

from game import Game, Card
from colorama import Fore, Back, Style
from ai import extract, genCols, AIPlayer, get52Card, get52Idx
import pandas as pd
import json
import random

#Keep track of good/bad/ok predictions
class Log:
    def __init__(self):
        self.bd = 0
        self.gd = 0
        self.k = 0
        self.last = 0
    
    def bad(self):
        self.bd = self.bd + 1
        self.last = -1

    def good(self):
        self.gd = self.gd + 1
        self.last = 1

    def ok(self):
        self.k = self.k + 1
        self.last = 0
    
    def asInt(self) -> list[int]:
        return [self.gd, self.k, self.bd]

    def asPct(self) -> list[float]:
        total = self.gd + self.bd + self.k
        total = 1 if total == 0 else total
        return [self.gd/total, self.k/total, self.bd/total]

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
        elif pile != None and pile.value == 13:
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

#Chooses a move from a move "object"
def chooseMove(move: dict, game: Game):
    if len(move) == 0:
        return False

    match move["cmd"]:
        case 'tt':
            if len(move) != 4:
                return False

            frm = int(move["frm"]) - 1
            to = int(move["to"]) - 1
            ct = int(move["ct"])

            if not game.move(frm, to, ct):
                return False
        case 'tc':
            if len(move) != 2:
                return False

            col = int(move["to"]) 

            if not game.collect(col):
                return False
        case 'd':
            if len(move) != 1:
                return False

            if not game.take():
                return False
        case 'pt':
            if len(move) != 2:
                return False

            to = int(move["to"]) - 1

            if not game.movePile(to):
                return False
        case 'pc':
            if len(move) != 1:
                return False

            if not game.collect(0):
                return False
        case 'ft':
            if len(move) != 3:
                return False

            suit = int(move["suit"]) - 1
            to = int(move["to"]) - 1

            if not game.moveFoundation(suit, to):
                return False
        case _:
            return False
    return True

#Returns the "best guess" card on the edge
def nearestCard(expected: Card, game_state: dict) -> Card:
    matches = {
        0: [], # A perfect match
        1: [], # Same color and value
        2: [], # Different color, same value
        3: []  # Different color and value
    }

    #Collect cards
    for t in range(0, 7):
        col = game_state["tableau"][t]
        if len(col) > 0:
            card = Card(col[-1]["suit"], col[-1]["value"])

            cat = 3
            if card == expected:
                cat = 0
            elif card.value == expected.value and card.suit % 2 == expected.suit % 2:
                cat = 1
            elif card.value == expected.value:
                cat = 2
            matches[cat].append(t + 1)
        elif expected.value == 0 and expected.suit == 0:
            matches[0].append(t + 1)

    #Return the best match
    for i in range(0, 4):
        for c in matches[i]:
            return c
    
    return Card(0,0)

#In a list of available moves, determine if a move is stored in it.
def isMoveAvailable(available: list, potential: dict):
    for move in available:
        if(move["cmd"] != potential["cmd"]):
            continue

        match potential["cmd"]:
            case 'tt':
                if move["to"] == potential["to"] and move["frm"] == potential["frm"] and move["ct"] == potential["ct"]:
                    return True
            case 'ft':
                if move["suit"] == potential["suit"] and move["to"] == potential["to"]:
                    return True
            case 'tc' | 'pt':
                if move["to"] == potential["to"]:
                    return True
            case 'd' | 'pc':
                return True
    return False

#Choose a move from available moves based on the predicted move
#Basically: fuzzy move -> real move

#Fuzzy moves are like this:
# tc 3 ([♥2])
# tt 38 
#They are based on the "to" column. This function finds the card they're talking about, and any corresponding data (like "frm" or "suit")
def decipherMove(pred_move: dict, available: list, game_state: dict, log: Log):
    matchingMove = [x for x in available if x["cmd"] == pred_move["cmd"]]

    #If there are no matching moves then just pick something at random
    if len(matchingMove) == 0:
        log.bad()
        return available[random.randint(0, len(available) - 1)]
    
    match pred_move["cmd"]:
        case 'tt':
            pred_to = nearestCard(get52Card(pred_move["to"]), game_state)

            #Determine from

            #Scan must go by row, starting at all cards adjacent to an unknown
            s = 0
            go = True
            while go:
                go = False
                for fcol, col in enumerate(game_state["tableau"]):
                    s_this = 0
                    for frow, rcardinfo in enumerate(col):
                        #Don't proceed if card is hidden or skip exceeded
                        if("hidden" in rcardinfo or  s_this < s):
                            continue
                        go = True
                        s_this = s_this + 1

                        #If this card can be added, return the move.
                        move = {
                            "cmd": "tt",
                            "frm": fcol + 1,
                            "to": pred_to,
                            "ct": len(col) - frow
                        }
                        if isMoveAvailable(matchingMove, move):
                            log.good()
                            return move
                s = s + 1

        #ft suit to
        case 'ft':
            pred_to = nearestCard(get52Card(pred_move["to"]), game_state)

            #Check which foundation cards can make the move
            for foundation in game_state["foundation"]:
                fd = Card(game_state["foundation"][foundation]["suit"], game_state["foundation"][foundation]["value"])
                move = {
                    "cmd": "ft",
                    "suit": fd.suit + 1,
                    "to": pred_to
                }
                if isMoveAvailable(matchingMove, move):
                    log.good()
                    return move
        #tc to
        #pt to
        case 'pt' | 'tc':
            pred_to = nearestCard(get52Card(pred_move["to"]), game_state)
            move = {
                "cmd": pred_move["cmd"],
                "to": pred_to
            }
            if isMoveAvailable(matchingMove, move):
                log.good()
                return move
        #pc
        #d
        case 'd' | 'pc':
            move = {
                "cmd": pred_move["cmd"]
            }
            if isMoveAvailable(matchingMove, move):
                log.good()
                return move

    #If nothing worked, choose random move from matching available moves.
    move = matchingMove[random.randint(0, len(matchingMove) - 1)]
    log.ok()
    return move

#Make a move fuzzy
def fuzzy(game_state: dict, move: dict):
    fuzzymove = {
        "cmd": move["cmd"]
    }
    match move["cmd"]:
        case 'tt' | 'tc' | 'ft' | 'pt':
            if len(game_state["tableau"][move["to"] - 1]) == 0:
                fuzzymove["to"] = 52
            else:
                cardinfo = game_state["tableau"][move["to"] - 1][-1]
                card = Card(cardinfo["suit"], cardinfo["value"])
                fuzzymove["to"] = get52Idx(card)

    return fuzzymove

#Create a move object from an input list
def moveFromInput(input: list) -> dict:
    match input[0]:
        case 'tt':
            if len(input) != 4 or any([not x.isdigit() for x in input[1:3]]):
                return {}

            return {"cmd": "tt", "frm": int(input[1]), "to": int(input[2]), "ct": int(input[3])}
        case 'ft':
            if len(input) != 3 or any([not x.isdigit() for x in input[1:2]]):
                return {}

            return {"cmd": "ft", "suit": int(input[1]), "to": int(input[2])}
        case 'tc':
            if len(input) != 2 or not input[1].isdigit():
                return {}

            return {"cmd": "tc", "to": int(input[1])}
        case 'pt':
            if len(input) != 2 or not input[1].isdigit():
                return {}

            return {"cmd": "pt", "to": int(input[1])}
        case 'pc':
            return {"cmd": "pc"}
        case 'd':
            return {"cmd": "d"}
        case 'json':
            return {"cmd": "json"}
    return {}

class Instance():
    def __init__(self):
        self.running = False
        print("inited")

    def refreshState(self):
        self.__state = self.__game.json()

    #Create a new instance
    def createNewInstance(self):
        self.__game = Game()
        self.__log = Log()
        self.__ai = AIPlayer()
        self.running = True
        self.refreshState()
    
    #Close the instance
    def close(self):
        #Only save if won
        if self.__game.win():
            self.__ai.save()

        self.running = False

    #Get the game state JSON
    def gameJson(self) -> dict:
        if not self.running:
            return {"error": "An instance of the game is not running."}
        return self.__state
    
    #Get the AI predicted move along with the actual move
    def ai_nextMove(self) -> dict:
        if not self.running:
            return {"error": "An instance of the game is not running."}
        state = extract(self.__state)
        pred_move = self.__ai.nextMove(state.to_frame().T)
        actual_move = decipherMove(pred_move, findAllMoves(self.__state), self.__state, self.__log)
        return {
            "pred_move": pred_move,
            "actual_move": actual_move,
            "accuracy": self.__log.last
        }
    
    #Get the accuracy of each AI model
    def ai_acc(self) -> dict:
        if not self.running:
            return {"error": "An instance of the game is not running."}
        return self.__ai.getAcc()
    
    #Perform a turn
    def turn(self, move: dict) -> dict:
        if not self.running:
            return {"error": "An instance of the game is not running."}
        
        if "cmd" not in move:
            return {"error": "No \"cmd\" found in move."}

        move_successful = chooseMove(move, self.__game)       
        won = self.__game.win()
        
        results: dict = {
            "move_successful": move_successful,
            "won": won
        }

        #Update game state
        self.refreshState()

        #If move was successful, log the move.
        if(move_successful):
            self.__ai.log(extract(self.__state), fuzzy(self.__state, move))

        #If won, close the game.
        if(won):
            accs = self.__log.asPct()
            results["good"] =  accs[0]
            results["ok"] =  accs[1]
            results["bad"] =  accs[2]
            self.close()
        
        return results


def main():
    inst = Instance()
    won = False
    while not won:
        if not inst.running:
            inst.createNewInstance()
        
        inst.__game.printGame()
        move = moveFromInput(input().strip().split(' '))
        outcome = inst.turn(move)

        if(outcome["won"]):
            won = True
    print(Fore.MAGENTA + "You win" + Fore.RESET)

if __name__ == "__main__":
    main()
