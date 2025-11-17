from game import Game, Card
from colorama import Fore, Back, Style
from ai import extract, genCols, numCmd, trainModel, numCmd_r
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
    cmd_predict = trainModel("data/cmd.csv", "Cmd")

    cols = genCols()
    cols.append('Cmd')
    data = pd.DataFrame(columns=cols)

    while not game.win():
        game.printGame()
        state = extract(json.loads(game.json()))
        pred_move = cmd_predict.predict(state.to_frame().T)
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