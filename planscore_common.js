//
// SHARED CONSTANTS
//

// the list of years to offer; used by the year picker so the user may choose dates
// note that not every state has data at all levels for every year
export const PLAN_YEARS = [
    1972, 1974, 1976, 1978,
    1980, 1982, 1984, 1986, 1988,
    1990, 1992, 1994, 1996, 1998,
    2000, 2002, 2004, 2006, 2008,
    2010, 2012, 2014, 2016,
];

// the color gradient from Republican red to Democrat blue
// see also lookupBiasColor() lookupBiasDescription() et al, which resolves a score (-1 to +1) into colors & descriptions
export const COLOR_GRADIENT = require('tinygradient').rgb(['#C71C36', '#F2E5FA', '#0049A8'], 100).map((tinycolor) => { return tinycolor.toHexString(); });

// technically bias scores range -1 to +1, but realistically we scale to a narrower band (25% bias is a lot!)
// this defines the spread to consider when scaling a score onto a color ramp or similar
// see also lookupBiasColor() lookupBiasDescription() et al, which resolves a score (-1 to +1) into colors & descriptions
export const BIAS_SPREAD_SCALING = 0.25;

// a bias <= this value will be considered balanced and below statistical significance
// see also lookupBiasColor() lookupBiasDescription() et al, which resolves a score (-1 to +1) into colors & descriptions
export const BIAS_BALANCED_THRESHOLD = 0.02;

// for remapping state name to a short code
export const STATE_NAME_TO_CODE = {
    'Alabama': 'AL',
    'Alaska': 'AK',
    'Arizona': 'AZ',
    'Arkansas': 'AR',
    'California': 'CA',
    'Colorado': 'CO',
    'Connecticut': 'CT',
    'Delaware': 'DE',
    'Florida': 'FL',
    'Georgia': 'GA',
    'Hawaii': 'HI',
    'Idaho': 'ID',
    'Illinois': 'IL',
    'Indiana': 'IN',
    'Iowa': 'IA',
    'Kansas': 'KS',
    'Kentucky': 'KY',
    'Louisiana': 'LA',
    'Maine': 'ME',
    'Maryland': 'MD',
    'Massachusetts': 'MA',
    'Michigan': 'MI',
    'Minnesota': 'MN',
    'Mississippi': 'MS',
    'Missouri': 'MO',
    'Montana': 'MT',
    'Nebraska': 'NE',
    'Nevada': 'NV',
    'New Hampshire': 'NH',
    'New Jersey': 'NJ',
    'New Mexico': 'NM',
    'New York': 'NY',
    'North Carolina': 'NC',
    'North Dakota': 'ND',
    'Ohio': 'OH',
    'Oklahoma': 'OK',
    'Oregon': 'OR',
    'Pennsylvania': 'PA',
    'Rhode Island': 'RI',
    'South Carolina': 'SC',
    'South Dakota': 'SD',
    'Tennessee': 'TN',
    'Texas': 'TX',
    'Utah': 'UT',
    'Vermont': 'VT',
    'Virginia': 'VA',
    'Washington': 'WA',
    'West Virginia': 'WV',
    'Wisconsin': 'WI',
    'Wyoming': 'WY',
};

// for remapping state short code to a name
export const STATE_CODE_TO_NAME = {
    'AL': 'Alabama',
    'AK': 'Alaska',
    'AZ': 'Arizona',
    'AR': 'Arkansas',
    'CA': 'California',
    'CO': 'Colorado',
    'CT': 'Connecticut',
    'DE': 'Delaware',
    'FL': 'Florida',
    'GA': 'Georgia',
    'HI': 'Hawaii',
    'ID': 'Idaho',
    'IL': 'Illinois',
    'IN': 'Indiana',
    'IA': 'Iowa',
    'KS': 'Kansas',
    'KY': 'Kentucky',
    'LA': 'Louisiana',
    'ME': 'Maine',
    'MD': 'Maryland',
    'MA': 'Massachusetts',
    'MI': 'Michigan',
    'MN': 'Minnesota',
    'MS': 'Mississippi',
    'MO': 'Missouri',
    'MT': 'Montana',
    'NE': 'Nebraska',
    'NV': 'Nevada',
    'NH': 'New Hampshire',
    'NJ': 'New Jersey',
    'NM': 'New Mexico',
    'NY': 'New York',
    'NC': 'North Carolina',
    'ND': 'North Dakota',
    'OH': 'Ohio',
    'OK': 'Oklahoma',
    'OR': 'Oregon',
    'PA': 'Pennsylvania',
    'RI': 'Rhode Island',
    'SC': 'South Carolina',
    'SD': 'South Dakota',
    'TN': 'Tennessee',
    'TX': 'Texas',
    'UT': 'Utah',
    'VT': 'Vermont',
    'VA': 'Virginia',
    'WA': 'Washington',
    'WV': 'West Virginia',
    'WI': 'Wisconsin',
    'WY': 'Wyoming',
};


//
// SHARED UTILITY FUNCTIONS
//

export const lookupBiasColor = (score) => {
    // for swatches, map a bias score onto the color ramp

    if (score === undefined || score === null) return '#FFFFFF';  // No Data

    // normalize the score onto an absolute scale from 0 (-max) to 1 (+max)
    // that gives us the index of the color gradient entry
    const bias_spread = BIAS_SPREAD_SCALING;
    let p_value = 0.5 + (0.5 * (score / bias_spread));
    if (p_value < 0) p_value = 0;
    else if (p_value > 1) p_value = 1;

    const i = Math.round((COLOR_GRADIENT.length - 1) * p_value);
    return COLOR_GRADIENT[i];
};

export const lookupBiasDescription = (score) => {
    // for swatches and titles, map a bias score onto some words describing it
    if (score === undefined || score === null) return 'No Data';

    const abscore = Math.abs(score);
    const whichparty = score > 0 ? 'Democrats' : 'Republicans';

    if (abscore >= 0.20) return `Most Biased In Favor of ${whichparty}`;
    if (abscore >= 0.14) return `More Biased In Favor of ${whichparty}`;
    if (abscore >= 0.07) return `Biased In Favor of ${whichparty}`;
    if (abscore >= BIAS_BALANCED_THRESHOLD) return `Slightly Biased In Favor of ${whichparty}`;
    return 'No Significant Bias';
};

export const lookupBiasFavorParty = (score) => {
    // just return the name of the party who is favored by this plan; or empty if it's balanced
    if (score === null || score === undefined) return '';
    if (Math.abs(score) <= BIAS_BALANCED_THRESHOLD) return '';
    return score > 0 ? 'Democrat' : 'Republican';
};
