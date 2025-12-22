import random
from colorama import Fore, Back, Style
import json

# Suits are:
# Hearts = H = 0
# Spades = S = 1
# Diamonds = D = 2
# Clubs = C = 3
class Card():
    def __init__(self, suit, value):
        self.suit = suit
        self.value = value
        self.discovered = value <= 0
    
    # Check if the given card can be appended to this card
    # Note: Prevent addition of cards that are 0
    def tryAdd(self, other) -> bool:
        return other.suit % 2 != self.suit % 2 and self.value - 1 == other.value and other.value > 0

    #Check if the given card is the next card (in context of a foundation)
    def tryNext(self, other) -> bool:
        return other.suit == self.suit and self.value + 1 == other.value

    #Return a string representing this card
    def __str__(self) -> str:
        #If not discovered, display card as unknown.
        if(self.discovered == False):
            return "[--]"
        suitstr = ""
        match self.suit:
            case 0:
                suitstr = '♥'
            case 1:
                suitstr = '♣'
            case 2:
                suitstr = '♦'
            case 3:
                suitstr = '♠'
            case _:
                suitstr = "?"

        valstr = ""
        match self.value:
            case 1:
                valstr = 'A'
            case 10:
                valstr = 'X'
            case 11:
                valstr = 'J'
            case 12:
                valstr = 'Q'
            case 13:
                valstr = 'K'
            case _:
                valstr = str(self.value)

        color = Fore.RED if self.suit % 2 == 0 else Fore.BLUE
        return f"{color}[{suitstr}{valstr}]{Fore.RESET}"
    
    def marshal(self):
        if(self.discovered):
            return {
                "suit": self.suit,
                "value": self.value
            }
        else:
            return {
                "hidden": True
            }

    #Discover a card
    def discover(self):
        self.discovered = True

    #Hide a card
    def hide(self):
        self.discovered = False

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.value == other.value

class Game():
    def __init__(self):
        #Tableau is 7 columns, where each column has # cards equal to its 1-based index
        self.tableau = []

        #Foundation has 1 stack of cards for all 4 suits, in value order.
        self.foundation = {}

        #Draw is a stack of cards that is looped through.
        self.draw = []

        #Pile is a stack of cards that were taken from draw. When draw is empty, pile becomes draw.
        self.pile = []

        self.initGame()

    #Initializes a game.
    #There are 13 different values for a card (A, 2-10!!, J, Q, K) and 4 suits (H, S, D, C) = 52 cards in a game
    def initGame(self):
        #Add all cards to an array
        cards = []
        for suit in range(0,4):
            for value in range(1, 14):
                cards.append(Card(suit, value))
        
        #Generate random card
        def genCard():
            card = cards[random.randint(0, len(cards) - 1)]
            cards.remove(card)
            return card

        #Generate foundation
        self.foundation[0] = Card(0, 0)
        self.foundation[1] = Card(1, 0)
        self.foundation[2] = Card(2, 0)
        self.foundation[3] = Card(3, 0)

        #Generate tableau
        for col in range(1,8):
            discolumn = []
            for row in range(0,col):
                discolumn.append(genCard())
            self.tableau.append(discolumn)
        
        #Generate draw
        #could probably just assign it but idk don't trust it will remain alive
        while(len(cards) > 0):
            card = cards.pop(random.randint(0, len(cards) - 1))
            self.draw.append(card) 
        
        self.discoverEdge()

    #Discover edge of tableau
    def discoverEdge(self):
        for i in range(0, 7):
            if len(self.tableau[i]) > 0:
                self.tableau[i][-1].discover()

    #Move a card from draw to pile
    def take(self):
        if(len(self.draw) > 0):
            card = self.draw.pop()
            card.discover()
            self.pile.append(card)
            return True
        else:
            while(len(self.pile) > 0):
                card = self.pile.pop()
                card.hide()
                self.draw.append(card)
            return len(self.draw) > 0
    #Attempt to collect a card from a column.
    #0 -> Pile
    #1-7 -> Tableau
    def collect(self, column):
        column = min(7, max(0, column)) 
        #Get card
        card = None
        if(column == 0 and len(self.pile) > 0):
            card = self.pile[-1]
        elif(column > 0 and len(self.tableau[column - 1]) > 0):
            card = self.tableau[column - 1][-1]

        #Check if next card. If so, update foundation
        if(card != None and self.foundation[card.suit].tryNext(card)):
            self.foundation[card.suit] = card

            #Remove card from game
            if(column == 0):
                self.pile.pop()
            else:
                self.tableau[column - 1].pop()
                self.discoverEdge()
            
            return True

        return False

    # Perform a literal move
    def performMove(self, frm, to, ct):
        for z in range(ct, 0, -1):
            self.tableau[to].append(self.tableau[frm].pop(-1*z))
        self.discoverEdge()

    # Determine if card [card] can be added to column [to]
    def canMove(self, to, card: Card) -> bool:
        return (len(self.tableau[to]) > 0 and self.tableau[to][-1].tryAdd(card)) or (len(self.tableau[to]) == 0 and card.value == 13)

    #Moves cards between tableau columns.
    #[ct] cards move from column [frm] to column [to]
    #Returns true if the move is valid, and false otherwise.
    def move(self, frm, to, ct):
        frm = min(6, max(0, frm)) 
        to = min(6, max(0, to)) 
        ct = min(ct, len(self.tableau[frm]))
        #Exit if there are no cards in to
        if(ct == 0):
            return False

        #Get target card
        target = self.tableau[frm][ct*-1]
        
        #If target was not discovered yet, then exit
        if(not target.discovered):
            return False

        #If there are cards in the to column
        if self.canMove(to, target):
            self.performMove(frm, to, ct)
            return True
        return False
    
    #Moves card at top of pile to column [to]
    def movePile(self, to):
        to = min(6, max(0, to)) 
        #If card can be added, perform add
        if(len(self.pile) > 0 and self.canMove(to, self.pile[-1])):
            top = self.pile.pop()
            self.tableau[to].append(top)
            self.discoverEdge()
            return True
        
        return False
    
    #Moves a card from [suit] to column [to]
    def moveFoundation(self, suit, to):
        to = min(6, max(0, to)) 
        suit = min(3, max(0, suit))
        fdCard = self.foundation[suit]
        if self.canMove(to, fdCard):
            self.tableau[to].append(fdCard)
            self.foundation[suit] = Card(fdCard.suit, fdCard.value - 1)
            self.foundation[suit].discover()
            return True
        return False
    
    #Check if the game was won
    def win(self):
        for suit in self.foundation:
            if self.foundation[suit].value != 13:
                return False
        return True

    def printGame(self):
        #Print foundation
        print(f"{"Foundation: ".ljust(15)}{self.foundation[0]} {self.foundation[1]} {self.foundation[2]} {self.foundation[3]}\n")

        #Print draw/pile
        drawstr = "    " if len(self.draw) <= 0 else self.draw[-1]
        pilestr = "" if len(self.pile) <= 0 else self.pile[-1]
        print(f"{drawstr} {pilestr}\n")

        #Print tableau columns
        print("[1 ] [2 ] [3 ] [4 ] [5 ] [6 ] [7 ]")

        #Print tableau
        go = True
        length = 0
        gstr = ""
        while(go):
            line = ""
            go = False
            for col in range(0,7):
                if len(self.tableau[col]) > length:
                    line = line + str(self.tableau[col][length]) + " "
                    go = True
                else:
                    line = line + "     "
            line = line.rjust(35, ' ') + '\n'
            gstr = gstr + line
            length = length + 1
        print(gstr)

    def json(self) -> dict:
        obj = {
            "tableau": [],
            "foundation": {
                "hearts": self.foundation[0].marshal(),
                "spades": self.foundation[1].marshal(),
                "diamonds": self.foundation[2].marshal(),
                "clubs": self.foundation[3].marshal(),
            },
            "draw": len(self.draw) > 0,
            "pile": False if len(self.pile) <= 0 else self.pile[-1].marshal()
        }

        for x in range(0,7):
            col = []
            for card in self.tableau[x]:
                col.append(card.marshal())
            obj["tableau"].append(col)
        
        return obj
        