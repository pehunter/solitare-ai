import React from 'react';

export interface Card_Data {
    suit?: number,
    value?: number,
    hidden?: boolean
}

export enum Card_Type {
    NORMAL = 0,
    HIDDEN,
    BLANK
}

export enum Card_Highlight {
    NONE = 0,
    FROM,
    TO
}

export type CardPos = {
    row: number,
    col: number, //If either is not -1, assume tableau. (if -1, then no card selected)
    suit: number, //If not -1, assume foundation is source (override r/c)
    pile: boolean //If true, assume pile is source (override everything)
}
const Card = (input: {data: Card_Data, highlight: Card_Highlight, select: (data: Card_Data, target: any) => void}) => {
    //Capture suit info
    let val = "";
    let symbol = "";
    let img = "";

    if(input.data.hidden == null && (input.data.value == null || input.data.value == -1))
        return <></>;

    if(input.data.hidden == null) {
        switch(input.data.suit) {
            //<3
            case 0:
                symbol = "♥";
                img = "♥️";
                break;
            case 1:
                symbol = "♣";
                img = "♣️";
                break;
            case 2:
                symbol = "♦";
                img = "♦️";
                break;
            case 3:
                symbol = "♠";
                img = "♠️";
                break;
        }

        switch(input.data.value) {
            case 1:
                val = "A";
                break;
            case 10:
                val = "J";
                break;
            case 11:
                val = "Q";
                break;
            case 12:
                val = "K";
                break;
            default:
                val = ""+input.data.value;
                break;
        }
    }

    //Card configuration
    let card_cls = "";
    let wrap_cls = "";
    if(input.data.hidden == true) {
        val = "";
        symbol = "";
        img = "";
        card_cls += "hidden ";
    //Suit & Value == 0 -> blank
    } else if(input.data.value == 0) {
        wrap_cls += "blank ";
        val = "?";
        symbol = ""
        img = "¿";
    }

    //Red suit
    if(input.data.value != 0 && (input.data.suit ? input.data.suit : 0) % 2 == 0)
        card_cls += "red ";

    //From glow
    if(input.highlight == Card_Highlight.FROM)
        wrap_cls += "glow-frm ";

    //To glow
    if(input.highlight == Card_Highlight.TO)
        wrap_cls += "glow-to ";

    return (<div className={wrap_cls + "wrapper"} onMouseDown={(e) => input.select(input.data, e.target)}>
                    <div className={card_cls + "card"}>
                        <div>{`${val}${symbol}`}</div>
                        <div className="icon">️{img}</div>
                        <div className="reverse">{`${val}${symbol}`}</div>
                    </div>
                </div>)
}

export default Card;