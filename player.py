from game import Game, Card
from colorama import Fore, Back, Style
from ai import extract, genCols, numCmd
import pandas as pd
import json

def chooseMove(move, game: Game):
    match move[0]:
        case 'tt':
            if len(move) != 4:
                return False

            frm = int(move[1]) - 1
            to = int(move[2]) - 1
            ct = int(move[3])

            if not game.move(frm, to, ct):
                return False
        case 'tc':
            if len(move) != 2:
                return False

            col = int(move[1]) 

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

            to = int(move[1]) - 1

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

            suit = int(move[1]) - 1
            to = int(move[2]) - 1

            if not game.moveFoundation(suit, to):
                return False
        case 'json':
            print(game.json())
            return True
        case _:
            return False
    return move[0]

def main():
    game = Game()
    data = pd.DataFrame(columns=genCols())
    while not game.win():
        game.printGame()
        state = extract(json.loads(game.json()))
        # print(Fore.YELLOW + str(data.info()) + Fore.RESET)

        move = input().split(' ')

        # print(move)
        if len(move) == 0:
            continue

        result = chooseMove(move, game)
        if result == False:
            print("Did not work")
        else:
            state.loc[0, 'Cmd'] = numCmd(move[0])
            data = pd.concat([data, state])


    #Save winning data!
    data.to_csv("output.csv", 'a')

    print(Fore.MAGENTA + "You ~~win~~!!! <3 👏👏👏👏")
    print("You are special." + Fore.RESET)

if __name__ == "__main__":
    main()