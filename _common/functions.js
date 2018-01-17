//
// SHARED UTILITY FUNCTIONS
//

import { BIAS_BALANCED_THRESHOLD } from './constants';
import { COLOR_GRADIENT } from './constants';
import { BIAS_SPREAD_SCALING } from './constants';


// return a structure of information about the given EG bias score: whether it's strong or weak, D or R, etc.
export const lookupBias = (score) => {
    if (score === undefined || score === null) return 'No Data';

    const abscore = Math.abs(score);

    const party = abscore > BIAS_BALANCED_THRESHOLD ? (score > 0 ? 'Democrat' : 'Republican') : '';
    const partycode = party.substr(0, 1).toLowerCase();

    let description = 'No Significant Bias';
    if (abscore >= 0.20) description = `Most Biased In Favor of ${party}`;
    if (abscore >= 0.14) description = `More Biased In Favor of ${party}`;
    if (abscore >= 0.07) description = `Biased In Favor of ${party}`;
    if (abscore >= BIAS_BALANCED_THRESHOLD) description = `Slightly Biased In Favor of ${party}`;

    let extremity = 0;
    if (abscore >= 0.14) extremity = 3;
    if (abscore >= 0.07) extremity = 2;
    if (abscore >= BIAS_BALANCED_THRESHOLD) extremity = 1;

    // normalize the score onto an absolute scale from 0 (-max) to 1 (+max); that gives us the index of the color gradient entry
    const bias_spread = BIAS_SPREAD_SCALING;
    let p_value = 0.5 + (0.5 * (score / bias_spread));
    if (p_value < 0) p_value = 0;
    else if (p_value > 1) p_value = 1;
    const color = COLOR_GRADIENT[ Math.round((COLOR_GRADIENT.length - 1) * p_value) ];

    return {
        party: party,
        partycode: partycode,
        color: color,
        extremity: extremity,
        description: description,
    };
};
