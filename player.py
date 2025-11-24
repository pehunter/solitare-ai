from game import Game, Card
from colorama import Fore, Back, Style
from ai import extract, genCols, AIPlayer, get48Card, get48Idx, findAllMoves
import pandas as pd
import json
import random

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
        case 'json':
            print(game.json())
            return True
        case _:
            return False

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

#Find the column/row index of a card
# def findFromCard(game_state: dict, card: Card):
#     for index, column in enumerate(game_state["tableau"]):
#         for rowi, cardinfo in enumerate(column):
#             if("hidden" not in cardinfo):
#                 foundCard = Card(cardinfo["suit"], cardinfo["value"])
#                 if(foundCard == card):
#                     return [index, len(column - rowi)]
#     return -1, -1

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
def decipherMove(pred_move: dict, available: list, game_state: dict):
    matchingMove = [x for x in available if x["cmd"] == pred_move["cmd"]]

    #If there are no matching moves then just pick something at random
    if len(matchingMove) == 0:
        print(Fore.RED + "Predicted move had no matching command, pick random..." + Fore.RESET)
        return available[random.randint(0, len(available) - 1)]
    
    match pred_move["cmd"]:
        case 'tt':
            pred_to = nearestCard(get48Card(pred_move["to"]), game_state)

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
                        if("hidden" in rcardinfo or  s_this > s):
                            continue
                        go = True

                        #If this card can be added, return the move.
                        move = {
                            "cmd": "tt",
                            "frm": fcol + 1,
                            "to": pred_to,
                            "ct": len(col) - frow
                        }
                        if isMoveAvailable(matchingMove, move):
                            print(Fore.GREEN + f"Perfectly deciphered {move["cmd"]} {move["frm"]} {move["to"]} {move["ct"]}" + Fore.RESET)
                            return move
                s = s + 1

        #ft suit to
        case 'ft':
            pred_to = nearestCard(get48Card(pred_move["to"]), game_state)

            #Check which foundation cards can make the move
            for foundation in game_state["foundation"]:
                fd = Card(foundation["suit"], foundation["value"])
                move = {
                    "cmd": "ft",
                    "suit": fd.suit + 1,
                    "to": pred_to
                }
                if isMoveAvailable(matchingMove, move):
                    print(Fore.GREEN + f"Perfectly deciphered {move["cmd"]} {move["suit"]} {move["to"]}" + Fore.RESET)
                    return move
        #tc to
        #pt to
        case 'pt' | 'tc':
            pred_to = nearestCard(get48Card(pred_move["to"]), game_state)
            move = {
                "cmd": pred_move["cmd"],
                "to": pred_to
            }
            if isMoveAvailable(matchingMove, move):
                print(Fore.GREEN + f"Perfectly deciphered {move["cmd"]} {move["to"]}" + Fore.RESET)
                return move
        #pc
        #d
        case 'd' | 'pc':
            move = {
                "cmd": pred_move["cmd"]
            }
            if isMoveAvailable(matchingMove, move):
                print(Fore.GREEN + f"Perfectly deciphered {move["cmd"]}" + Fore.RESET)
                return move

    #If nothing worked, choose random move from matching available moves.
    move = matchingMove[random.randint(0, len(matchingMove) - 1)]
    print(Fore.YELLOW + f"Could not fully decipher move, choosing a random {move["cmd"]}" + Fore.RESET)
    return move

#Make a move fuzzy
def fuzzy(game_state: dict, move: dict):
    fuzzymove = {
        "cmd": move["cmd"]
    }
    match move["cmd"]:
        case 'tt' | 'tc' | 'ft' | 'pt':
            if len(game_state["tableau"][move["to"] - 1]) == 0:
                fuzzymove["to"] = 48
            else:
                cardinfo = game_state["tableau"][move["to"] - 1][-1]
                card = Card(cardinfo["suit"], cardinfo["value"])
                fuzzymove["to"] = get48Idx(card)

    return fuzzymove

#Create a move object from an input list
def moveFromInput(input: list) -> dict:
    match input[0]:
        case 'tt':
            if len(input) != 4:
                return {}

            return {"cmd": "tt", "frm": int(input[1]), "to": int(input[2]), "ct": int(input[3])}
        case 'ft':
            if len(input) != 3:
                return {}

            return {"cmd": "ft", "suit": int(input[1]), "to": int(input[2])}
        case 'tc':
            if len(input) != 2:
                return {}

            return {"cmd": "tc", "to": int(input[1])}
        case 'pt':
            if len(input) != 2:
                return {}

            return {"cmd": "pt", "to": int(input[1])}
        case 'pc':
            return {"cmd": "pc"}
        case 'd':
            return {"cmd": "d"}
        case 'json':
            return {"cmd": "json"}
    return {}

def main():
    game = Game()
    # cmd_predict = trainModel("data/cmd.csv", "Cmd")
    ai = AIPlayer()

    # cols = genCols()
    # cols.append('Cmd')
    # data = pd.DataFrame(columns=cols)

    while not game.win():
        game.printGame()
        gs = json.loads(game.json())
        state = extract(gs)
        pred_move = ai.nextMove(state.to_frame().T)
        print(Fore.MAGENTA + f"Predicting  {pred_move}" + Fore.RESET)
        decipherMove(pred_move, findAllMoves(gs), gs)
        # print(Fore.YELLOW + str(data.info()) + Fore.RESET)

        move = moveFromInput(input().strip().split(' '))

        # print(move)
        # if len(move) == 0:
            # continue

        result = chooseMove(move, game)
        if result == False:
            print("Did not work")
        else:
            fz = fuzzy(gs, move)
            ai.log(state, fuzzy(gs, move))
            deciph = decipherMove(fz, findAllMoves(gs), gs)
            # state['Cmd'] = numCmd(move[0])
            # data = pd.concat([data, state.to_frame().T])


    #Save winning data!
    ai.save()
    # data.to_csv("data/cmd.csv", mode='a', header=False)

    print(Fore.MAGENTA + "You ~~win~~!!! <3 👏👏👏👏")
    print("You are special." + Fore.RESET)

if __name__ == "__main__":
    main()
