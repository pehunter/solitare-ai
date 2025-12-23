import React, { useEffect, useState } from 'react';
import Tableau, { Tableau_Data } from './Tableau';
import Pile from './Pile';
import Foundation, {Foundation_Data} from './Foundation';
import { Card_Data, CardPos } from './Card';
import DragCard from './DragCard';
import AIStats, {AccList, getBlankAccList} from './AI_Stats'

type GameState = {
    foundation: Foundation_Data,
    pile: (Card_Data | boolean),
    draw: boolean,
    tableau: Tableau_Data
}

export type Move = {
    "cmd": string,
    "frm"?: number,
    "to"?: number,
    "ct"?: number,
    "suit"?: number,
}

function getCP(row: number = -1, col: number = -1, suit: number = 0, pile: boolean = false) {
    return {row: row, col: col, suit: suit, pile: pile}
}

//Returns the "blank" game state
function getBlankGame(): GameState {
    return {
        foundation: {
            "hearts": {"value": -1},
            "spades": {"value": -1},
            "diamonds": {"value": -1},
            "clubs": {"value": -1},
        },
        pile: false,
        draw: false,
        tableau: [[]]
    };
}

//Returns a "blank"/invalid move
function getBlankMove(): Move {
    return {"cmd": "_"}
}

const App = () => {
    const [x, setX] = useState(0)
    const [y, setY] = useState(0)
    const [offX, setOffX] = useState(0);
    const [offY, setOffY] = useState(0);
    const [dragging, setDrag] = useState(false)
    const [dragData, setDragData] = useState<Card_Data>({suit: -1, value: -1})
    const [selectedPos, setSelectedPos] = useState<CardPos>(getCP())
    const [state, setGameState] = useState<GameState>(getBlankGame());
    const [aiMove, setAIMove] = useState<Move>(getBlankMove());
    const [ai_foundation, setAIFoundation] = useState<number>(-1);
    const [ai_acc, setAIAcc] = useState<AccList>(getBlankAccList());
    const [ai_quality, setAIQuality] = useState<number>(0);
    const [stem, setURLStem] = useState<string>("localhost:8888");

    async function getGameState() {
        fetch(`http://${stem}/get/state`)
        .then((data: Response) =>  {
            return data.json()})
        .then((jsonData: any) => {
            if(jsonData == undefined || "error" in jsonData)
                setGameState(getBlankGame());
            else
                setGameState(jsonData as GameState);
        })
        .catch((rsn: any) => alert(":(" + rsn))
    }

    //Get next move from AI
    async function getAIMove() {
        return fetch(`http://${stem}/get/ai_move`)
        .then((data: Response) =>data.json())
        .then((jsonData: any) => {
            if(jsonData == undefined || "error" in jsonData) {
                setAIQuality(0);
                setAIMove(getBlankMove());
                return false;
            } else {
                setAIQuality(jsonData.accuracy);
                setAIMove(jsonData.actual_move);
                console.log(jsonData.actual_move);
                return true;
            }
        })
        .catch((rsn: any) => setAIMove(getBlankMove()))
    }

    //Attempt to perform a move
    async function makeMove(move: Move) {
        fetch(`http://${stem}/act/move`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(move)
        }).then((resp: Response) => resp.json())
        .then((results: any) => {
            if(results.won)
                alert("You won")
            setTimeout(refresh, 25);
        }).catch((reason: any) => console.log(reason))
    }

    //Manage game instances
    async function startGame() {
        fetch(`http://${stem}/act/start`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({"close": true})

        })
        .then((data: Response) =>data.json())
        .then((jsonData: any) => {
            if("msg" in jsonData) {
                alert(jsonData["msg"]);
                setTimeout(refresh, 25);
            } else
                alert(jsonData["error"]);
        })
        // .catch((rsn: any) => alert(rsn))
    }

    //Train the model
    async function trainModel() {
        fetch(`http://${stem}/act/train`, {
            method: "POST",
            body: ""
        })
        .then((data: Response) =>data.json())
        .then((jsonData: any) => {
            if("msg" in jsonData) {
                alert(jsonData["msg"]);
            } else
                alert(jsonData);
        })
        // .catch((rsn: any) => alert(rsn))
    }

    //Get AI accuracies
    async function getAccuracy() {
        fetch(`http://${stem}/get/ai_acc`)
        .then((data: Response) =>data.json())
        .then((jsonData: any) => {
            if("error" in jsonData)
                alert(jsonData["error"]);
            else
                setAIAcc(jsonData as AccList);
        })
        // .catch((rsn: any) => alert(rsn))
    }

    //JSlop function
    function move(cp: null | CardPos = null): Move {
        //If null, return draw command.
        if(cp == null)
            return {
                "cmd": "d"
            }

        //Initial selection is from pile
        if(selectedPos.pile == true) {
            //Pile -> Tableau = pt
            if(cp.row == 1 && cp.col > -1) {
                return {
                    "cmd": "pt",
                    "to": cp.col
                }
            }

            //Pile -> Foundation = pc
            if(cp.suit > 0) {
                return {
                    "cmd": "pc"
                }
            }
        
        //From foundation
        } else if(selectedPos.suit > 0) {
            //Foundation -> Tableau = ft
            if(cp.row == 1 && cp.col > -1) {
                return {
                    "cmd": "ft",
                    "suit": selectedPos.suit,
                    "to": cp.col
                }
            }
        }
        //From tableau
        else if(selectedPos.col > -1 && selectedPos.row > -1) {
            //Tableau -> Tableau = tt
            if(cp.row == 1 && cp.col > -1) {
                return {
                    "cmd": "tt",
                    "frm": selectedPos.col,
                    "to": cp.col,
                    "ct": selectedPos.row
                }
            }

            //Tableau -> Foundation = tc 
            if(cp.suit > 0) {
                return {
                    "cmd": "tc",
                    "to": selectedPos.col
                }
            }
        }

        return getBlankMove();
    }


    //Ran when a card is clicked. Contains the card's group, row/col, card info, and HTML <wrapper> object.
    function cardSelected(type: string, row: number, col: number, cardData: Card_Data, obj: any) {
        let offsetX: number = x - obj.offsetLeft;
        let offsetY: number = y - obj.offsetTop;
        
        let cp: CardPos;
        switch(type) {
            case "foundation": 
                cp = getCP(-1,-1,row);
                break;
            case "tableau": 
                cp = getCP(row, col);
                break;
            case "draw":
                if(dragging)
                    return;
                //Send command directly
                let d = move();
                makeMove(d);
                return;
            case "pile":
                cp = getCP(-1, -1, 0, true);
                break;
            default:
                return;
        }

        manageDrag(cardData, offsetX, offsetY, cp);
    }

    //Update x and y upon mouse move
    function captureMouse(e: any) {
      //Get X and Y
      setX(e.clientX);
      setY(e.clientY);
    }


    //Handles selecting cards and performing actions based off of selection
    function manageDrag(data: Card_Data, offsetX: number, offsetY: number, cp: CardPos) {
        let clear = false;

        //First selection
        if (!dragging) {
          //Edge case 1: Draw hidden. If draw is selected, send draw command without dragging.
          if(!(data.hidden ?? false) && (data.value ?? 0) > 0) {
            //Load selected card as dragged card
            setDragData(data);
            setDrag(true);
            setOffX(offsetX);
            setOffY(offsetY);
            setSelectedPos(cp);
            console.log("selected..");
          }

          //Second selection: do things here
        } else {
          let mv_obj = move(cp);
          makeMove(mv_obj);
          clear = true;
        }

        //Clear drag data if requested
        if(clear) {
          setDragData({ suit: -1, value: -1 });
          setDrag(false);
          setSelectedPos(getCP());
        }
    }

    function refresh() {
        getGameState()
        getAIMove()
        getAccuracy();
    }

    useEffect(() => {
        setURLStem(window.location.href.split('/')[2]);
    }, []);
    
    //Refresh on stem change
    useEffect(() => {
        // alert(stem);
        refresh()
    }, [stem])
 
    return (
      <div style={{position: 'absolute', width: '100%'}} onMouseMove={(e) => captureMouse(e)}>
        <div className="top">
            <Pile draw_data={state.draw} pile_data={state.pile} card_sel={cardSelected} sel_pos={selectedPos} ai_move={aiMove} set_ai_foundation={setAIFoundation}/>
            <button id="start" onClick={startGame}>Start</button>
            <button id="train" onClick={trainModel}>Train</button>
            <Foundation foundation_data={state.foundation} card_sel={cardSelected} sel_pos={selectedPos} ai_move={aiMove} ai_foundation={ai_foundation}/>
        </div>
        <Tableau tableau_data={state.tableau} card_sel={cardSelected} sel_pos={selectedPos} ai_move={aiMove} set_ai_foundation={setAIFoundation}/>
        <DragCard data={dragData} x={x} y={y} offX={offX} offY={offY}/>
        <AIStats quality={ai_quality} accs={ai_acc} />
      </div>
    );
}

export default App;