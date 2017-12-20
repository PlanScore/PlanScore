/******/ (function(modules) { // webpackBootstrap
/******/ 	// The module cache
/******/ 	var installedModules = {};
/******/
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/
/******/ 		// Check if module is in cache
/******/ 		if(installedModules[moduleId]) {
/******/ 			return installedModules[moduleId].exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = installedModules[moduleId] = {
/******/ 			i: moduleId,
/******/ 			l: false,
/******/ 			exports: {}
/******/ 		};
/******/
/******/ 		// Execute the module function
/******/ 		modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/
/******/ 		// Flag the module as loaded
/******/ 		module.l = true;
/******/
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/
/******/
/******/ 	// expose the modules object (__webpack_modules__)
/******/ 	__webpack_require__.m = modules;
/******/
/******/ 	// expose the module cache
/******/ 	__webpack_require__.c = installedModules;
/******/
/******/ 	// identity function for calling harmony imports with the correct context
/******/ 	__webpack_require__.i = function(value) { return value; };
/******/
/******/ 	// define getter function for harmony exports
/******/ 	__webpack_require__.d = function(exports, name, getter) {
/******/ 		if(!__webpack_require__.o(exports, name)) {
/******/ 			Object.defineProperty(exports, name, {
/******/ 				configurable: false,
/******/ 				enumerable: true,
/******/ 				get: getter
/******/ 			});
/******/ 		}
/******/ 	};
/******/
/******/ 	// getDefaultExport function for compatibility with non-harmony modules
/******/ 	__webpack_require__.n = function(module) {
/******/ 		var getter = module && module.__esModule ?
/******/ 			function getDefault() { return module['default']; } :
/******/ 			function getModuleExports() { return module; };
/******/ 		__webpack_require__.d(getter, 'a', getter);
/******/ 		return getter;
/******/ 	};
/******/
/******/ 	// Object.prototype.hasOwnProperty.call
/******/ 	__webpack_require__.o = function(object, property) { return Object.prototype.hasOwnProperty.call(object, property); };
/******/
/******/ 	// __webpack_public_path__
/******/ 	__webpack_require__.p = "";
/******/
/******/ 	// Load entry module and return exports
/******/ 	return __webpack_require__(__webpack_require__.s = 118);
/******/ })
/************************************************************************/
/******/ ({

/***/ 118:
/***/ (function(module, exports, __webpack_require__) {

"use strict";


var _slicedToArray = function () { function sliceIterator(arr, i) { var _arr = []; var _n = true; var _d = false; var _e = undefined; try { for (var _i = arr[Symbol.iterator](), _s; !(_n = (_s = _i.next()).done); _n = true) { _arr.push(_s.value); if (i && _arr.length === i) break; } } catch (err) { _d = true; _e = err; } finally { try { if (!_n && _i["return"]) _i["return"](); } finally { if (_d) throw _e; } } return _arr; } return function (arr, i) { if (Array.isArray(arr)) { return arr; } else if (Symbol.iterator in Object(arr)) { return sliceIterator(arr, i); } else { throw new TypeError("Invalid attempt to destructure non-iterable instance"); } }; }();

function _toConsumableArray(arr) { if (Array.isArray(arr)) { for (var i = 0, arr2 = Array(arr.length); i < arr.length; i++) { arr2[i] = arr[i]; } return arr2; } else { return Array.from(arr); } }

// this page's HTML template with the [hash] cache-buster
// and the only stylesheet
__webpack_require__(12);
__webpack_require__(65);

// polyfills
//require('core-js/fn/array/includes');

// bundle some local/vendor libraries
//require('./js/leaflet-control-basemapbar.js');
//require('./js/leaflet-control-basemapbar.css');

//
// CONSTANTS
//

// the currently-visible state: boundary type + year, e.g. US House districts for 1984
// these are affected by window.selectXXX() family of functions which ultimately are all wrappers over loadDataForSelectedBoundaryAndYear()
var CURRENT_VIEW = {};

// the list of years to offer; used by the year picker so the user may choose dates
// note that not every state has data at all levels for every year
var PLAN_YEARS = [1972, 1974, 1976, 1978, 1980, 1982, 1984, 1986, 1988, 1990, 1992, 1994, 1996, 1998, 2000, 2002, 2004, 2006, 2008, 2010, 2012, 2014, 2016];

// the list of states, for mapping ABBR => NAME, for populating selectors, ...
var STATES = {
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
    'WY': 'Wyoming'
};

// the bias numbers fitting into each colorful bucket
// used for the map choropleth, for the legend, other charts, ...
// the from/to/color are specifically for Highcharts, so don't rename them, but you could add more fields to suit other consumers
// the magical value -999999 represents No Data and will always be the first in this series
// see also renderMapLegend() which generates the legend
// see also loadDataForSelectedBoundaryAndYear() which assigns the color ramp for choropleth
var MAP_CHOROPLETH_BREAKS = [{ from: -999999, to: -100, color: '#FFFFFF', title: 'No Data' }, { from: -100, to: -0.20, color: '#C71C36', title: 'Most Biased Toward Republican' }, { from: -0.20, to: -0.10, color: '#D95F72', title: 'More Biased Toward Republican' }, { from: -0.10, to: -0.05, color: '#E8A2AD', title: 'Somewhat Biased Toward Republican' }, { from: -0.05, to: -0.02, color: '#F5D7DC', title: 'Slightly Biased Toward Republican' }, { from: -0.02, to: 0.02, color: '#F2E5FA', title: 'Balanced' }, { from: 0.02, to: 0.05, color: '#D7E4F5', title: 'Slightly Biased Toward Democrat' }, { from: 0.05, to: 0.10, color: '#99B7DE', title: 'Somewhat Biased Toward Democrat' }, { from: 0.10, to: 0.20, color: '#4C7FC2', title: 'More Biased Toward Democrat' }, { from: 0.20, to: 100, color: '#0049A8', title: 'Most Biased Toward Democrat' }];

// when generating tooltips, a certain skew will be considered balanced and below statistical significance
// this would correspond to the Balanced choropleth break defined above (+X to -X is still balanced)
var BIAS_BALANCED_THRESHOLD = 0.02;

//
// PAGE STARTUP / INIT FUNCTIONS
//

$(document).ready(function () {
    initYearPickers();
    initStatePicker();
    initBoundaryPicker();
    initLoadStartingConditions(); // this will implicitly call loadDataForSelectedBoundaryAndYear() after setup, loading the map

    $(window).on('resize', handleResize);
    handleResize();
});

window.initYearPickers = function () {
    // there are 2 year pickers: mobile and full-size
    // mobile is a simple SELECT element and changing it selects a year
    // desktop is a fancy series of HTML/CSS dots which can be clicked to select a year
    // both of these connect to selectYear()

    var $picker_small = $('#yearpicker-small');
    PLAN_YEARS.slice().reverse().forEach(function (year) {
        $('<option></option>').text(year).prop('value', year).appendTo($picker_small);
    });
    $picker_small.change(function () {
        var year = $(this).val();
        selectYear(year);
    });

    var $picker_big = $('#yearpicker-big');
    PLAN_YEARS.forEach(function (year) {
        // each button has some utility classes so we can call out certain landmark years
        // see also handleResize() which adjusts the full-width spacing behavior
        var $button = $('<a></a>').attr('data-year', year).prop('href', '#').prop('title', 'Show partisan bias analysis for ' + year).appendTo($picker_big);
        if (year % 10 === 0) $button.addClass('decade');
        if (year % 4 === 0) $button.addClass('presidential');
    });
    $('<br/>').appendTo($picker_big);
    PLAN_YEARS.filter(function (year) {
        return year % 10 === 0;
    }).forEach(function (year) {
        // now add the decade years
        // see also handleResize() which adjusts the full-width spacing behavior
        $('<span class="yearlabel"></span>').text(year).attr('data-year', year).appendTo($picker_big);
    });
    $picker_big.on('click', 'a', function () {
        var year = $(this).attr('data-year');
        selectYear(year);
    });
};

window.initStatePicker = function () {
    // state picker is the UI for selectState() to show a popup for the given state
    var $picker = $('#statepicker');
    $('<option></option>').text('(select state)').prop('value', '').appendTo($picker);
    var _iteratorNormalCompletion = true;
    var _didIteratorError = false;
    var _iteratorError = undefined;

    try {
        for (var _iterator = Object.entries(STATES)[Symbol.iterator](), _step; !(_iteratorNormalCompletion = (_step = _iterator.next()).done); _iteratorNormalCompletion = true) {
            var _step$value = _slicedToArray(_step.value, 2),
                stateabbr = _step$value[0],
                statename = _step$value[1];

            $('<option></option>').text(statename).prop('value', stateabbr).appendTo($picker);
        }
    } catch (err) {
        _didIteratorError = true;
        _iteratorError = err;
    } finally {
        try {
            if (!_iteratorNormalCompletion && _iterator.return) {
                _iterator.return();
            }
        } finally {
            if (_didIteratorError) {
                throw _iteratorError;
            }
        }
    }

    $picker.change(function () {
        var stateabbr = $(this).val();
        selectState(stateabbr);
    });

    // when the modal closes, also explicitly select no state so as to reset the UI
    $('#stateinfo-modal').on('hidden.bs.modal', function (e) {
        selectState(null);
    });
};

window.initBoundaryPicker = function () {
    $('#boundarypicker div').click(function () {
        var boundarytype = $(this).attr('data-boundary');
        selectBoundaryType(boundarytype);
    });
};

window.initLoadStartingConditions = function () {
    // the most recent year and the first listed district type; select them for us
    selectYear(PLAN_YEARS[PLAN_YEARS.length - 1]);
    selectBoundaryType('ushouse');
};

window.handleResize = function () {
    // various things that don't gracefully handle being resized, so we need to help them out

    // the big year picker is a series of dots, and we want it to span the screen
    // calculate the usable width by subtracting the width of each dot
    // then the right-margin per dot, by diviging space by number of dots
    var $picker_big = $('#yearpicker-big');
    var $picker_big_buttons = $picker_big.find('a');

    var usable_width = $picker_big.width();
    $picker_big_buttons.each(function () {
        var consumed_width = $(this).width() + 4; // width() doesn't include border; we know these have 2px border
        usable_width -= consumed_width;
    });

    var rightspace = usable_width / ($picker_big_buttons.length - 1);
    $picker_big_buttons.css({
        'margin-right': rightspace + 'px' // CSS enforces 0 for the last dot-button
    });

    // the big year picker has SPAN items with the years, which we want aligned to the decade dots we just positioned above
    $picker_big.find('span.yearlabel').each(function () {
        var year = $(this).text();
        var $button = $picker_big_buttons.filter('[data-year="' + year + '"]');
        var left = $button.position().left - $button.width() / 3;
        $(this).css({ left: left + 'px', top: '40px' });
    });
};

//
// RUNTIME FUNCTIONS FOR CHANGING YEAR + DISTRICT TYPE + STATE INFO
// loadDataForSelectedBoundaryAndYear() is the real worker here; the others are basically convenience functions
//

window.loadDataForSelectedBoundaryAndYear = function () {
    if (!CURRENT_VIEW.year || !CURRENT_VIEW.boundtype) return; // need both; during startup one will be blank, so avoid an error

    // if there's a map already, destroy it
    var existing_map = $('#map').data('mapchart');
    if (existing_map) {
        existing_map.destroy();
        $('#map').data('mapchart', null);
    }

    // initialize the bias score statistics to -999999 No Data all around
    // expected data structure: list of states and their bias ratings
    var chartdata = [];
    var _iteratorNormalCompletion2 = true;
    var _didIteratorError2 = false;
    var _iteratorError2 = undefined;

    try {
        for (var _iterator2 = Object.entries(STATES)[Symbol.iterator](), _step2; !(_iteratorNormalCompletion2 = (_step2 = _iterator2.next()).done); _iteratorNormalCompletion2 = true) {
            var _step2$value = _slicedToArray(_step2.value, 2),
                stateabbr = _step2$value[0],
                statename = _step2$value[1];

            chartdata.push({
                abbr: stateabbr,
                name: statename,
                value: -999999
            });
        }

        // fetch the CSV file
    } catch (err) {
        _didIteratorError2 = true;
        _iteratorError2 = err;
    } finally {
        try {
            if (!_iteratorNormalCompletion2 && _iterator2.return) {
                _iterator2.return();
            }
        } finally {
            if (_didIteratorError2) {
                throw _iteratorError2;
            }
        }
    }

    var url = '../data/bias_' + CURRENT_VIEW.boundtype + '.csv';
    Papa.parse(url, {
        download: true,
        header: true,
        complete: function complete(results) {
            // filter by the year (geography is implicit by which CSV was fetched)
            // and for each row assign the bias score to the state's row in the above
            // this is loop-within-loop as we match arrays to arrays, but P=50 and Q=20ish so it's affordable
            results = results.data.forEach(function (row) {
                if (row.year != CURRENT_VIEW.year) return; // wrong year; next
                chartdata.filter(function (datarow) {
                    return datarow.abbr == row.state;
                })[0].value = parseFloat(row.bias);
            });
            renderMapWithNewData(chartdata);
            renderMapLegend();
        }
    });

    function renderMapWithNewData(data) {
        // attach this raw data into the chart DIV so we can access it later
        // see also selectState() which needs to access the compiled data
        $('#map').data('biasdata', data);

        // render the map chart
        var newmapchart = Highcharts.mapChart('map', {
            chart: {
                borderWidth: 0
            },
            title: {
                text: '' // no big title
            },
            legend: {
                enabled: false // we have a custom-crafted label
            },

            colorAxis: {
                dataClasses: MAP_CHOROPLETH_BREAKS
            },

            tooltip: { // the tooltips are kept minimal, as most info is in a popup when clicked and mobile folks can't use tooltips effectively
                formatter: function formatter() {
                    if (this.point.value === -999999) return this.key + ': No data';
                    return this.key + ': Click for details';
                }
            },

            series: [{
                // use the Highcharts-provided US states, joining on their "postal-code" to our "abbr"
                data: data,
                mapData: Highcharts.maps['countries/us/us-all'],
                joinBy: ['postal-code', 'abbr'],

                // click events: call the popup maker
                events: {
                    click: function click(e) {
                        selectState(e.point.abbr);
                    }
                }
            }]
        });

        // stow that reference so we can destroy it on next data load
        $('#map').data('mapchart', newmapchart);
    }

    function renderMapLegend() {
        var $legend = $('<div class="legend"></div>').appendTo('#map');

        var legend_slices = [].concat(_toConsumableArray(MAP_CHOROPLETH_BREAKS.slice(1)), [MAP_CHOROPLETH_BREAKS[0]]);

        $('<h1>Most biased plan in our data</h1>').appendTo($legend);
        $('<h2>(based on efficiency gap)</h2>').appendTo($legend);

        legend_slices.forEach(function (legendentry, i, allslices) {
            var $slice = $('<div class="slice"></div>').css({ 'background-color': legendentry.color }).prop('title', legendentry.title).appendTo($legend);
            if (i === 0) {
                // first real slice = R
                $slice.append('<span>R</span>');
            } else if (i === allslices.length - 2) {
                // last real slice = D
                $slice.append('<span>D</span>');
            }
        });

        $('<h5>No Data</h5>').appendTo($legend); // last slice will be the No Data, here are the words to go with it
    }
};

window.selectYear = function (year) {
    // UI update: highlight this button
    $('#yearpicker-big a').removeClass('active').filter('[data-year="' + year + '"]').addClass('active');

    // save to the state and refresh the map + data
    CURRENT_VIEW.year = year;
    loadDataForSelectedBoundaryAndYear();
};

window.selectBoundaryType = function (boundtype) {
    // UI update: highlight this button
    $('#boundarypicker div').removeClass('active').filter('[data-boundary="' + boundtype + '"]').addClass('active');

    // save to the state and refresh the map + data
    CURRENT_VIEW.boundtype = boundtype;
    loadDataForSelectedBoundaryAndYear();
};

window.selectState = function (stateabbr) {
    // note that blank is an acceptable option to select no state at all
    if (!stateabbr) stateabbr = '';

    // UI update: set the selector
    $('#statepicker').val(stateabbr);

    // show/hide the popup
    if (stateabbr) {
        // fetch the info from the map, and attach some attributes for the popup
        // tip: shallow copy via slice() so as not to mutate the existing one
        var biasinfo = $('#map').data('biasdata').filter(function (statedata) {
            return statedata.abbr === stateabbr;
        }).slice(0, 1)[0];

        // add to the info, an analysis
        if (biasinfo.value === -999999) {
            biasinfo.analysis = 'No data available.';
        } else if (Math.abs(biasinfo.value) <= BIAS_BALANCED_THRESHOLD) {
            biasinfo.analysis = 'This plan shows no statistically significant skew toward either party.';
        } else if (biasinfo.value < 0) {
            // R bias
            biasinfo.analysis = 'This plan is more biased than <b>' + (50 + Math.round(Math.abs(biasinfo.value) * 100)) + '%</b> plans analyzed.<br/>This plan is biased in favor of <b>Republican</b> voters.';
        } else {
            // must be D bias
            biasinfo.analysis = 'This plan is more biased than <b>' + (50 + Math.round(Math.abs(biasinfo.value) * 100)) + '%</b> of plans analyzed.<br/>This plan is biased in favor of <b>Democrat</b> voters.';
        }

        // the URL for more info: the state name, mangled for URLs e.g. south_carolina
        var moreinfourl = '../' + biasinfo.name.toLowerCase().replace(/\W/g, '_') + '/';

        // open the modal and do the string replacements
        var $modal = $('#stateinfo-modal').modal('show');
        $modal.find('span[data-field="statename"]').html(biasinfo.name);
        $modal.find('span[data-field="analysis"]').html(biasinfo.analysis);
        $modal.find('.modal-footer a').prop('href', moreinfourl);
    } else {
        // nothing to do, except I guess close the modal if it happens to be open
        $('#stateinfo-modal').modal('hide');
    }
};

//
// OTHER RUNTIME FUNCTIONS
//

/***/ }),

/***/ 12:
/***/ (function(module, exports) {

// removed by extract-text-webpack-plugin

/***/ }),

/***/ 65:
/***/ (function(module, exports, __webpack_require__) {

module.exports = __webpack_require__.p + "home/index.html";

/***/ })

/******/ });
//# sourceMappingURL=index.js.map