import React from 'react';
import Card, { Card_Highlight, Card_Data, CardPos } from './Card';
import { Move } from './App';

export type Tableau_Data = Card_Data[][]

const Tableau = (input: {tableau_data: Tableau_Data, card_sel: (type: string, row: number, col: number, data: Card_Data, obj: any) => void, sel_pos: CardPos, ai_move: Move, set_ai_foundation: (suit: number) => void}) => {
    
    //Get card highlight based on current ai_move. Also handles setting foundation
    function getHighlight(row: number, col: number, card: Card_Data): Card_Highlight {
        
        //From for tt: will highlight the card if the "frm" and "ct" match the row/col
        if(input.ai_move.cmd == "tt" && input.ai_move.frm != undefined && input.ai_move.to != undefined && input.ai_move.ct != undefined) {
            if(input.ai_move.frm == col && input.ai_move.ct == row)
                return Card_Highlight.FROM;
        }
        
        //Tc: will highlight the frm in the tableau and set the ai_foundation to the card's suit, highlighting the foundation.
        if(input.ai_move.cmd == "tc" && input.ai_move.to != undefined && col == input.ai_move.to && row == 1) {
            input.set_ai_foundation(card.suit ?? -1)
            return Card_Highlight.FROM;
        }

        //To: For tt, pt, and ft, it will highlight the tableau card if it is an edge card in the correct column
        if(input.ai_move.cmd in ["tt", "pt", "ft"] && input.ai_move.to != undefined && input.ai_move.to == col && row == 1) {
            return Card_Highlight.TO;
        }

        return Card_Highlight.NONE;
    }
    //Iterate columns
    let tableau = input.tableau_data.map((cold, col) => {
        //Iterate rows of column
        let rows: any[] = [];

        const game_col = col + 1;
        cold.forEach((card, row) => {
            const game_row = cold.length - row;
            //If card is moving, don't render it.
            if(input.sel_pos.col != game_col || input.sel_pos.row < game_row)  {
                let selectCard = (data: Card_Data, obj: any) => {
                    input.card_sel("tableau", game_row, game_col, data, obj);
                }

                rows.push(<Card data={card} highlight={getHighlight(game_row, game_col, card)} select={selectCard}/>);
            }
        })

        if(rows.length == 0) {
            let dato = {suit: -1, value: 0};
            rows.push(<Card data={dato} highlight={getHighlight(1, game_col, dato)} select={(data: Card_Data, obj: any) => {
                input.card_sel("tableau", 1, game_col, data, obj)
            }}/>);
        }

        let height = 12 + 3*(rows.length - 1);
        return <div style={{maxHeight: `${height}em`}} className="tableau-col">
            {rows}
        </div>
    })

    return (<div id="tableau" className="tableau">
            {tableau}         
        </div>)
}

export default Tableau;