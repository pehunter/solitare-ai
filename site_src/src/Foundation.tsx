import React from 'react';
import Card, { Card_Data, Card_Highlight, CardPos } from './Card';
import { Move } from './App';

export type Foundation_Data = {
    "hearts": Card_Data,
    "spades": Card_Data,
    "diamonds": Card_Data,
    "clubs": Card_Data,
}

function suit_to_str(suit: number) {
    switch(suit) {
        case 1: return "hearts";
        case 2: return "spades";
        case 3: return "diamonds";
        case 4: return "clubs";
        default: return "";
    }
}

const Foundation = (input: {foundation_data: Foundation_Data, card_sel: (type: string, row: number, col: number, data: Card_Data, obj: any) => void, sel_pos: CardPos, ai_move: Move, ai_foundation: number}) => {
    function genSelectFunc(data: Card_Data, obj: any) {
        input.card_sel("foundation", (data.suit || 0) + 1, -1, data, obj);
    }

    //Get the highlight for the foundation card
    function getHighlight(suit: number): Card_Highlight {
        //If the current move is pc or tc and this card is the matching foundation, highlight it.
        if(["pc", "tc"].includes(input.ai_move.cmd) && input.ai_foundation == suit)
            return Card_Highlight.TO;
        //If performing a foundation transfer and this card matches the move's suit, highlight it.
        else if(input.ai_move.cmd == "ft" && input.ai_move.suit != undefined && input.ai_move.suit == suit)
            return Card_Highlight.FROM;

        return Card_Highlight.NONE;
    }

    let processed: Foundation_Data = {
        ...input.foundation_data
    };

    let grabbed_suit = suit_to_str(input.sel_pos.suit);
    if(grabbed_suit != "")
        processed[grabbed_suit as keyof Foundation_Data] = {suit: -1, value: 0}


    return (
        <div id="foundation" className="foundation">
            <Card data={processed.hearts} highlight={getHighlight(1)} select={genSelectFunc}/>
            <Card data={processed.spades} highlight={getHighlight(2)} select={genSelectFunc}/>
            <Card data={processed.diamonds} highlight={getHighlight(3)} select={genSelectFunc}/>
            <Card data={processed.clubs} highlight={getHighlight(4)} select={genSelectFunc}/>
        </div>
    );
}

export default Foundation;