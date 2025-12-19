import React from 'react';
import Tableau, { Tableau_Data } from './Tableau';
import Pile from './Pile';
import Foundation, {Foundation_Data} from './Foundation';
import Card, { Card_Data, Card_Highlight } from './Card';

export type AccList = {
    "cmd": number,
    "tt": number,
    "ft": number,
    "tc": number,
    "pt": number
}

export function getBlankAccList(): AccList {
    return {
        "cmd": 0,
        "tt": 0,
        "ft": 0,
        "tc": 0,
        "pt": 0 
    }
}

const AIStats = (input: {quality: number, accs: AccList}) => {
    let cls = (() => {
        switch(input.quality) {
            case -1: return "bad";
            case 0: return "ok";
            case 1: return "good";
        }
    })()

    console.log(cls);

    return <div className="col">
        <text className={cls}>{cls}</text>
        <text>{`cmd accuracy: ${input.accs["cmd"]}%`}</text>
        <text>{`tt accuracy: ${input.accs["tt"]}%`}</text>
        <text>{`ft accuracy: ${input.accs["ft"]}%`}</text>
        <text>{`tc accuracy: ${input.accs["tc"]}%`}</text>
        <text>{`pt accuracy: ${input.accs["pt"]}%`}</text>
    </div>
}

export default AIStats;