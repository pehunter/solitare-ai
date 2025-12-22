### ai.py
### Handles data processing, data extraction, and move prediction

from game import Card, Game
from colorama import Fore
# from player import chooseMove
import pprint
import random
import pandas as pd
import numpy as np
from sklearn import linear_model, model_selection, metrics
import joblib

#Get the card's index in a 52 equation
def get52Idx(card: Card):
    return card.suit*13 + (card.value - 1)

#Get card from the 52 index
def get52Card(index: int):
    if index == 52:
        return Card(0,0)

    suit = int(index/13)
    value = (index % 13) + 1
    return Card(suit, value)

def get52Title(index: int):
    suit = int(index/13)
    match suit:
        case 0: suit = 'H'
        case 1: suit = 'S'
        case 2: suit = 'D'
        case 3: suit = 'C'
    
    value = (index % 13) + 1
    match value:
        case 1: value = 'A'
        case 10: value = 'X'
        case 11: value = 'J'
        case 12: value = 'Q'
        case 13: value = 'K'
        case _: value = value
    return f"{suit}{value}"

#Generate the columns for Pandas DF
def genCols():
    #Generate columns
    cols = []
    for c in range(0, 52):
        t = get52Title(c)
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
# 1. All end cards at bottom of stack (52)
# 2. All cards at top of stack (52)
# 3. All movable cards (52)
# 4. Collected cards (52)
# 5. Top of foundation (52)
# 6. Top of pile (52)
# 7. Cards in draw? (1)
# 8. Empty space available? (1)
def extract(data: dict) -> pd.Series:
    cols = genCols()
    cardData = pd.Series(data=np.zeros(len(cols), dtype=np.int8), index=cols)
    empty = False
    draw = False

    for col in data["tableau"]:
        if len(col) > 0:
            #Set bottom card
            bottom = Card(col[-1]["suit"], col[-1]["value"])
            cardData["Bottom_"+get52Title(get52Idx(bottom))]= 1

            #Set top card
            x = 0
            while "hidden" in col[x]:
                x = x + 1
            top = Card(col[x]["suit"], col[x]["value"])
            cardData["Top_"+get52Title(get52Idx(top))]= 1
            #Get middle cards
            while x < len(col):
                middle = Card(col[x]["suit"], col[x]["value"])
                cardData["Move_"+get52Title(get52Idx(middle))]= 1
                x = x + 1
        else:
            empty = True
    
    for suit in data["foundation"]:
        val = data["foundation"][suit]["value"]
        for z in range(1, val + 1):
            card = Card(data["foundation"][suit]["suit"], z)
            cardData["Collect_"+get52Title(get52Idx(card))]= 1
        if(val > 0):
            card = Card(data["foundation"][suit]["suit"], val)
            cardData["Foundation_"+get52Title(get52Idx(card))]= 1

    if(data["pile"] != False):
        pile = Card(data["pile"]["suit"], data["pile"]["value"])
        cardData["Pile_"+get52Title(get52Idx(pile))]= 1
    
    if(data["draw"]):
        draw = True

    cardData["Empty"] = int(empty)
    cardData["Draw"] = int(draw)
    
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

def trainModel(cmd: str, outCol: str):
    #Load CSV into df
    x = pd.read_csv(f"data/{cmd}.csv", header=0, index_col=0)

    #Capture x and y & drop outCol
    y = x.loc[:, outCol]
    x = x.drop([outCol], axis=1)

    #Train/test
    x_train, x_test, y_train, y_test = model_selection.train_test_split(x, y, random_state=612, test_size=0.25, shuffle=True)


    #Create LR
    logr = linear_model.LogisticRegression(max_iter=612)
    logr.fit(x_train,y_train)

    #Save LR
    joblib.dump(logr, f"model/{cmd}.pkl")

    #Test LR
    y_pred = logr.predict(x_test)
    acc = metrics.accuracy_score(y_test, y_pred)

    #Save test results
    with open(f"model/{cmd}.acc", "w") as file:
        file.write(str(acc))

# Load a model from a saved file
def loadModel(cmd: str):
    return None, 0
    logr = joblib.load(f"model/{cmd}.pkl")
    
    #Get accuracy
    acc = -1
    with open(f"model/{cmd}.acc", "r") as file:
        acc = float(file.read())
    
    return logr, acc

#Get columns from first line of csv
def getColumns(csvPath: str):
    with open(csvPath) as csv:
        return csv.readline().split(',')
    return []

class AIPlayer():
    def __init__(self):
        #Load models
        self.cmdModel, cmdAcc = loadModel("cmd")
        self.ttModel, ttAcc = loadModel("tt")
        self.ptModel, ptAcc = loadModel("pt")
        self.tcModel, tcAcc = loadModel("tc")
        self.ftModel, ftAcc = loadModel("ft")

        #Save accuracy
        self.acc = {
            "cmd": cmdAcc,
            "tt": ttAcc,
            "pt": ptAcc,
            "tc": tcAcc,
            "ft": ftAcc,
        }

        #Setup dataframes for collected data
        basecols = genCols()
 
        self.cmdData = pd.DataFrame(columns=(basecols + ['Cmd']))
        self.ttData = pd.DataFrame(columns=(basecols + ['Card']))
        self.ptData = pd.DataFrame(columns=(basecols + ['Card']))
        self.tcData = pd.DataFrame(columns=(basecols + ['Card']))
        self.ftData = pd.DataFrame(columns=(basecols + ['Card']))
    
    #Get accuracies for the 5 models
    def getAcc(self):
        return self.acc

    #Predict next move based on game state
    def nextMove(self, gameState: pd.DataFrame):
        #What to do
        move = {}
        return move

        cmd = self.cmdModel.predict(gameState)

        match cmd:
            #'tt'
            case 0:
                move['cmd'] = 'tt'
                to = self.ttModel.predict(gameState)
                move['to'] = int(to[0])
            #'tc'
            case 1:
                move['cmd'] = 'tc'
                to = self.tcModel.predict(gameState)
                move['to'] = int(to[0])
            #'d'
            case 2:
                move['cmd'] = 'd'
            #'pt'
            case 3:
                move['cmd'] = 'pt'
                to = self.ptModel.predict(gameState)
                move['to'] = int(to[0])
            #'pc'
            case 4:
                move['cmd'] = 'pc'
            #'ft'
            case 5:
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