// the list of years to offer; used by the year picker so the user may choose dates
// note that not every state has data at all levels for every year
export const PLAN_YEARS = [
    1972, 1974, 1976, 1978,
    1980, 1982, 1984, 1986, 1988,
    1990, 1992, 1994, 1996, 1998,
    2000, 2002, 2004, 2006, 2008,
    2010, 2012, 2014, 2016,
];

// the bias numbers fitting into each colorful bucket
// used for the map choropleth, for the legend, other charts, ...
// the from/to/color are specifically for Highcharts, so don't rename them, but you could add more fields to suit other consumers
// the magical value -999999 represents No Data and will always be the first in this series
// see also renderMapLegend() which generates the legend
// see also loadDataForSelectedBoundaryAndYear() which assigns the color ramp for choropleth
//gda to be removed per #83
export const MAP_CHOROPLETH_BREAKS = [
    { from: -999999, to: -100, color: '#FFFFFF', title: 'No Data' },
    { from: -100, to: -0.20, color: '#C71C36', title: 'Most Biased Toward Republican' },
    { from: -0.20, to: -0.10, color: '#D95F72', title: 'More Biased Toward Republican' },
    { from: -0.10, to: -0.05, color: '#E8A2AD', title: 'Somewhat Biased Toward Republican' },
    { from: -0.05, to: -0.02, color: '#F5D7DC', title: 'Slightly Biased Toward Republican' },
    { from: -0.02, to: 0.02, color: '#F2E5FA', title: 'Balanced' },
    { from: 0.02, to: 0.05, color: '#D7E4F5', title: 'Slightly Biased Toward Democrat' },
    { from: 0.05, to: 0.10, color: '#99B7DE', title: 'Somewhat Biased Toward Democrat' },
    { from: 0.10, to: 0.20, color: '#4C7FC2', title: 'More Biased Toward Democrat' },
    { from: 0.20, to: 100, color: '#0049A8', title: 'Most Biased Toward Democrat' },
];

// the color gradient from Republican red to Democrat blue
// see also the shared function lookupBiasColor() which resolves a score (-1 to +1) into a color from this gradient
// see also the shared function lookupBiasDescription()which resolves a score (-1 to +1) into a descriptive phrase
export const COLOR_GRADIENT = require('tinygradient').rgb(['red', 'blue'], 30).map((tinycolor) => { return tinycolor.toHexString(); });

// when generating tooltips, a certain skew will be considered balanced and below statistical significance
// this would correspond to the Balanced choropleth break defined above (+X to -X is still balanced)
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
