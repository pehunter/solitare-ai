from game import Game, Card
from colorama import Fore, Back, Style

def chooseMove(move, game: Game):
    match move[0]:
        case 'tt':
            if len(move) != 4:
                return False

            frm = int(move[1]) - 1
            to = int(move[2]) - 1
            ct = int(move[3])

            return game.move(frm, to, ct)
        case 'tc':
            if len(move) != 2:
                return False

            col = int(move[1]) 

            return game.collect(col)
        case 'd':
            if len(move) != 1:
                return False

            return game.take()
        case 'pt':
            if len(move) != 2:
                return False

            to = int(move[1]) - 1

            return game.movePile(to)
        case 'pc':
            if len(move) != 1:
                return False

            return game.collect(0)
        case 'ft':
            if len(move) != 3:
                return False

            suit = int(move[1]) - 1
            to = int(move[2]) - 1

            return game.moveFoundation(suit, to)
        case 'json':
            print(game.json())
            return True
        case _:
            return False

def main():
    game = Game()
    while not game.win():
        game.printGame()
        move = input().split(' ')

        print(move)
        if len(move) == 0:
            continue

        if not chooseMove(move, game):
            print("Did not work")


    print(Fore.MAGENTA + "You ~~win~~!!! <3 👏👏👏👏")
    print("You are special." + Fore.RESET)

if __name__ == "__main__":
    main()