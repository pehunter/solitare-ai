import React from 'react';
import Tableau, { Tableau_Data } from './Tableau';
import Pile from './Pile';
import Foundation, {Foundation_Data} from './Foundation';
import Card, { Card_Data, Card_Highlight } from './Card';

const DragCard = (input: {data: Card_Data, x: number, y: number, offX: number, offY: number}) => {
    let card;
    
    //Don't render cards that aren't at least ace!
    if((input.data.value || 0) > 0) {
      card = <div style={{left: input.x - input.offX, top: input.y - input.offY}} id="dragCard" className="drag">
        <Card data={input.data} highlight={Card_Highlight.NONE} select={(data: Card_Data) => {}}/>
      </div>

    }

    return card;
}

export default DragCard;