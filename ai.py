from game import Card, Game
from colorama import Fore
# from player import chooseMove
import pprint
import json
import random
import pandas as pd
import numpy as np
from sklearn import linear_model, model_selection, metrics

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
        elif pile != None and pile.value == 12:
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

#Get card from the 48 index
def get48Card(index: int):
    if index == 48:
        return Card(0,0)

    suit = int(index/12)
    value = (index % 12) + 1
    return Card(suit, value)

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
def extract(data: dict) -> pd.Series:
    cols = genCols()
    cardData = pd.Series(data=np.zeros(len(cols), dtype=np.int8), index=cols)
    empty = False
    draw = False

    #Is this even needed?
    hidden = 0

    for col in data["tableau"]:
        if len(col) > 0:
            #Set bottom card
            bottom = Card(col[-1]["suit"], col[-1]["value"])
            cardData["Bottom_"+get48Title(get48Idx(bottom))]= 1

            #Set top card
            x = 0
            while "hidden" in col[x]:
                hidden = hidden + 1
                x = x + 1
            top = Card(col[x]["suit"], col[x]["value"])
            # cardData[get48Idx(top)][1] = 1
            cardData["Top_"+get48Title(get48Idx(top))]= 1
            #Get middle cards
            while x < len(col):
                middle = Card(col[x]["suit"], col[x]["value"])
                # cardData[get48Idx(middle)][2] = 1
                cardData["Move_"+get48Title(get48Idx(middle))]= 1
                x = x + 1
        else:
            empty = True
    
    for suit in data["foundation"]:
        val = data["foundation"][suit]["value"]
        for z in range(1, val + 1):
            card = Card(data["foundation"][suit]["suit"], z)
            cardData["Collect_"+get48Title(get48Idx(card))]= 1
            # cardData[get48Idx(card)][3] = 1
        if(val > 0):
            card = Card(data["foundation"][suit]["suit"], val)
            cardData["Foundation_"+get48Title(get48Idx(card))]= 1
            # cardData[get48Idx(card)][4] = 1

    if(data["pile"] != False):
        pile = Card(data["pile"]["suit"], data["pile"]["value"])
        cardData["Pile_"+get48Title(get48Idx(pile))]= 1
        # cardData[get48Idx(pile)][5] = 1
    
    if(data["draw"]):
        draw = True
    # print(cardData)
    # print(f"Hidden: {hidden}")
    # print(f"Empty: {empty}")
    # print(f"Draw: {draw}")


    cardData["Empty"] = int(empty)
    cardData["Draw"] = int(draw)
    # shaped = np.append(cardData, [empty, draw, 9])
    # shaped = np.reshape(shaped, (1, 48*6 + 3))
    # df = pd.DataFrame(shaped, columns=cols)
    
    return cardData

def numCmd(cmd: str):
    match cmd:
        case 'tt': return 0
        case 'tc': return 1
        case 'd': return 2
        case 'pt': return 3
        case 'pc': return 4
        case 'ft': return 5
        case _: return 6

def numCmd_r(idx: int):
    match idx:
        case 0: return 'tt'
        case 1: return 'tc'
        case 2: return 'd'
        case 3: return 'pt'
        case 4: return 'pc'
        case 5: return 'ft'
        case 6: return '_'

def trainModel(csvPath: str, outCol: str):
    #Load CSV into df
    x = pd.read_csv(csvPath, header=0, index_col=0)

    #Capture x and y & drop outCol
    y = x.loc[:, outCol]
    x = x.drop([outCol], axis=1)

    #Train/test
    x_train, x_test, y_train, y_test = model_selection.train_test_split(x, y, random_state=612, test_size=0.25, shuffle=True)


    #Create LR
    logr = linear_model.LogisticRegression(max_iter=612)
    logr.fit(x_train,y_train)

    #Test LR
    y_pred = logr.predict(x_test)
    acc = metrics.accuracy_score(y_test, y_pred)
    print(Fore.BLUE + f"Model \"{outCol}\" achieved an accuracy of {acc*100}%" + Fore.RESET)

    #Return
    return logr

#Get columns from first line of csv
def getColumns(csvPath: str):
    with open(csvPath) as csv:
        return csv.readline().split(',')
    return []

class AIPlayer():
    def __init__(self):
        #Load models
        self.cmdModel = trainModel("data/cmd.csv", "Cmd")
        self.ttModel = trainModel("data/tt.csv", "Card")
        self.ptModel = trainModel("data/pt.csv", "Card")
        self.tcModel = trainModel("data/tc.csv", "Card")
        self.ftModel = trainModel("data/ft.csv", "Card")

        #Setup dataframes for collected data
        basecols = genCols()
        cards = [str(x) for x in list(range(48))]

        self.cmdData = pd.DataFrame(columns=(basecols + ['Cmd']))
        self.ttData = pd.DataFrame(columns=(basecols + ['Card']))
        self.ptData = pd.DataFrame(columns=(basecols + ['Card']))
        self.tcData = pd.DataFrame(columns=(basecols + ['Card']))
        self.ftData = pd.DataFrame(columns=(basecols + ['Card']))
    
    #Predict next move based on game state
    def nextMove(self, gameState: pd.DataFrame):
        cmd = self.cmdModel.predict(gameState)

        #What to do
        move = {}

        match cmd:
            #'tt'
            case 0:
                #TT stuff here
                move['cmd'] = 'tt'
                to = self.ttModel.predict(gameState)
                move['to'] = to
            #'tc'
            case 1:
                #TC stuff here
                move['cmd'] = 'tc'
                to = self.tcModel.predict(gameState)
                move['tc'] = to
            #'d'
            case 2:
                move['cmd'] = 'd'
            #'pt'
            case 3:
                #PT stuff here
                move['cmd'] = 'pt'
                to = self.ptModel.predict(gameState)
                move['pt'] = to
            #'pc'
            case 4:
                move['cmd'] = 'pc'
            #'ft'
            case 5:
                #FT stuff here
                move['cmd'] = 'ft'
                to = self.ftModel.predict(gameState)
                move['ft'] = to
            case _:
                print("An unknown move was selected?")
        
        return move
    
    #Log moves into CSVs
    def log(self, state: pd.Series, move: dict):
        #Cmd
        cmdState = state.copy()
        cmdState['Cmd'] = numCmd(move["cmd"])
        self.cmdData = pd.concat([self.cmdData, cmdState.to_frame().T])

        #Set column correctly
        if move["cmd"] in ('tt', 'pt', 'tc', 'ft'):
            subcmdState = state.copy()
            subcmdState['Card'] = move["to"]
            
            #Save to correct model
            match move["cmd"]:
                case 'tt':
                    self.ttData = pd.concat([self.ttData, subcmdState.to_frame().T])
                case 'ft':
                    self.ftData = pd.concat([self.ftData, subcmdState.to_frame().T])
                case 'pt':
                    self.ptData = pd.concat([self.ptData, subcmdState.to_frame().T])
                case 'tc':
                    self.tcData = pd.concat([self.tcData, subcmdState.to_frame().T])

    #Save data to CSVs
    def save(self):
        self.cmdData.to_csv("data/cmd.csv", mode='a', header=False)
        self.ttData.to_csv("data/tt.csv", mode='a', header=False)
        self.tcData.to_csv("data/tc.csv", mode='a', header=False)
        self.ptData.to_csv("data/pt.csv", mode='a', header=False)
        self.ftData.to_csv("data/ft.csv", mode='a', header=False)
