import React from 'react';

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

    return <div className="col">
        <text className={cls}>{cls}</text>
        <text>{`cmd accuracy: ${Math.round(input.accs["cmd"]*10000)/100}%`}</text>
        <text>{`tt accuracy: ${Math.round(input.accs["tt"]*10000)/100}%`}</text>
        <text>{`ft accuracy: ${Math.round(input.accs["ft"]*10000)/100}%`}</text>
        <text>{`tc accuracy: ${Math.round(input.accs["tc"]*10000)/100}%`}</text>
        <text>{`pt accuracy: ${Math.round(input.accs["pt"]*10000)/100}%`}</text>
    </div>
}

export default AIStats;