import React from 'react';
import Card, { Card_Data, Card_Highlight, CardPos } from './Card';

const Pile = (input: {draw_data: boolean, pile_data: (Card_Data | boolean), card_sel: (type: string, row: number, col: number, data: Card_Data, obj: any) => void, sel_pos: CardPos, ai_move: Move, set_ai_foundation: (suit: number) => void}) => {
    //Draw card
    const draw_card_data = {
        "suit": 0,
        "value": 0,
        "hidden": input.draw_data
    }

    let pile_en = input.pile_data === false || input.sel_pos.pile;

    //Pile card; if False, make blank
    let pd: Card_Data;
    if(pile_en) {
        pd = {
            "suit": 0,
            "value": 0,
            "hidden": false
        }

    } else {
        pd = input.pile_data as Card_Data;
    }

    //Selector functions
    function genPD(type: string) {
        if(input.sel_pos.pile)
            return (x: Card_Data, y: any) => {};

        return (data: Card_Data, obj: any) => {
            input.card_sel(type, -1, -1, data, obj);
        }
    }

    //Highlight function
    function getHighlight(type: string): Card_Highlight {
        //Highlight draw
        if(input.ai_move.cmd == "d" && type === "draw")
            return Card_Highlight.TO;
        
        //Highlight pile
        if(["pc", "pt"].includes(input.ai_move.cmd) && type === "pile") {
            console.log("uhh");
            return Card_Highlight.FROM;
        }
        
        return Card_Highlight.NONE;
    }

    return <div id="pile" className="pile">
            <Card data={draw_card_data} highlight={getHighlight("draw")} select={genPD("draw")}/>
            <Card data={pd} highlight={getHighlight("pile")} select={genPD("pile")}/>
    </div>
    

}

export default Pile;