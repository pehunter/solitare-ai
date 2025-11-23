from game import Game, Card
from colorama import Fore, Back, Style
from ai import extract, genCols, numCmd, trainModel, numCmd_r, AIPlayer, get48Card
import pandas as pd
import json
import random

#Chooses a move from a move "object"
def chooseMove(move: dict, game: Game):
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
    return move[0]

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
    
    #Return the best match
    for i in range(0, 4):
        for c in matches[i]:
            return c
    
    return Card(0,0)

#Find the column/row index of a card
def findFromCard(game_state: dict, card: Card):
    for index, column in enumerate(game_state["tableau"]):
        for rowi, cardinfo in enumerate(column):
            if("hidden" not in cardinfo):
                foundCard = Card(cardinfo["suit"], cardinfo["value"])
                if(foundCard == card):
                    return [index, len(column - rowi)]
    return -1, -1

#In a list of available moves, determine if a move is stored in it.
def isMoveAvailable(available: list, potential: dict):
    for move in available:
        if(move["cmd"] != potential[0]):
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
            tcol, trow = findFromCard(game_state, pred_to)

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
                        card = Card(rcardinfo["suit"], rcardinfo["value"])
                        #If this card can be added, return the move.
                        move = {
                            "cmd": "tt",
                            "frm": fcol + 1,
                            "to": tcol + 1,
                            "ct": len(col) - frow
                        }
                        if isMoveAvailable(matchingMove, move):
                            print(Fore.GREEN + f"Perfectly deciphered {pred_move["cmd"]} {pred_move["frm"]} {pred_move["to"]} {pred_move["ct"]}" + Fore.RESET)
                            return move
                s = s + 1

        #ft suit to
        case 'ft':
            pred_to = nearestCard(get48Card(pred_move["to"]), game_state)
            col, _ = findFromCard(game_state, pred_to)

            #Check which foundation cards can make the move
            for foundation in game_state["foundation"]:
                fd = Card(foundation["suit"], foundation["value"])
                move = {
                    "cmd": "ft",
                    "suit": fd.suit + 1,
                    "to": col + 1
                }
                if isMoveAvailable(matchingMove, move):
                    print(Fore.GREEN + f"Perfectly deciphered {pred_move["cmd"]} {pred_move["suit"]} {pred_move["to"]}" + Fore.RESET)
                    return move
        #tc to
        #pt to
        case 'pt' | 'tc':
            pred_to = nearestCard(get48Card(pred_move["to"]), game_state)
            col, _ = findFromCard(game_state, pred_to)
            move = {
                "cmd": pred_move["cmd"],
                "to": col + 1
            }
            if isMoveAvailable(matchingMove, move):
                print(Fore.GREEN + f"Perfectly deciphered {pred_move["cmd"]} {pred_move["to"]}" + Fore.RESET)
                return move
        #pc
        #d
        case 'd' | 'pc':
            move = {
                "cmd": pred_move["cmd"]
            }
            if isMoveAvailable(matchingMove, move):
                print(Fore.GREEN + f"Perfectly deciphered {pred_move["cmd"]}" + Fore.RESET)
                return move

    #If nothing worked, choose random move from matching available moves.
    move = matchingMove[random.randint(0, len(matchingMove) - 1)]
    print(Fore.YELLOW + f"Could not fully decipher move, choosing a random {move["cmd"]}" + Fore.RESET)
    return move

#Create a move object from an input list
def moveFromInput(input: list):
    match input[0]:
        case 'tt':
            if len(input) != 4:
                return {}

            return {"cmd": "tt", "frm": input[1], "to": input[2], "ct": input[3]}
        case 'ft':
            if len(input) != 3:
                return {}

            return {"cmd": "ft", "suit": input[1], "to": input[2]}
        case 'tc':
            if len(input) != 2:
                return {}

            return {"cmd": "tc", "to": input[1]}
        case 'pt':
            if len(input) != 2:
                return {}

            return {"cmd": "pt", "to": input[1]}
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

    cols = genCols()
    cols.append('Cmd')
    data = pd.DataFrame(columns=cols)

    while not game.win():
        game.printGame()
        state = extract(json.loads(game.json()))
        pred_move = ai.cmdModel.predict(state.to_frame().T)
        print(Fore.MAGENTA + f"Predicting  {numCmd_r(pred_move[0])}" + Fore.RESET)
        # print(Fore.YELLOW + str(data.info()) + Fore.RESET)

        move = input().split(' ')

        # print(move)
        if len(move) == 0:
            continue

        result = chooseMove(move, game)
        if result == False:
            print("Did not work")
        else:
            state['Cmd'] = numCmd(move[0])
            data = pd.concat([data, state.to_frame().T])


    #Save winning data!
    data.to_csv("data/cmd.csv", mode='a', header=False)

    print(Fore.MAGENTA + "You ~~win~~!!! <3 👏👏👏👏")
    print("You are special." + Fore.RESET)

if __name__ == "__main__":
    main()