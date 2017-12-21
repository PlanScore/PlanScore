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
/******/ 	return __webpack_require__(__webpack_require__.s = 155);
/******/ })
/************************************************************************/
/******/ ({

/***/ 102:
/***/ (function(module, exports, __webpack_require__) {

module.exports = __webpack_require__.p + "washington/index.html";

/***/ }),

/***/ 155:
/***/ (function(module, exports, __webpack_require__) {

"use strict";


// this page's HTML template with the [hash] cache-buster
// and the only stylesheet
__webpack_require__(49);
__webpack_require__(102);

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

// the bias numbers fitting into each colorful bucket
// used for the map choropleth, for the legend, other charts, ...
// the from/to/color are specifically for Highcharts, so don't rename them, but you could add more fields to suit other consumers
// the magical value -999999 represents No Data and will always be the first in this series
// see also renderMapLegend() which generates the legend
// see also loadDataForSelectedBoundaryAndYear() which assigns the color ramp for choropleth
var MAP_CHOROPLETH_BREAKS = [{ from: -999999, to: -100, color: '#FFFFFF', title: 'No Data' }, { from: -100, to: -0.20, color: '#C71C36', title: 'Most Biased Toward Republican' }, { from: -0.20, to: -0.10, color: '#D95F72', title: 'More Biased Toward Republican' }, { from: -0.10, to: -0.05, color: '#E8A2AD', title: 'Somewhat Biased Toward Republican' }, { from: -0.05, to: -0.02, color: '#F5D7DC', title: 'Slightly Biased Toward Republican' }, { from: -0.02, to: 0.02, color: '#F2E5FA', title: 'Balanced' }, { from: 0.02, to: 0.05, color: '#D7E4F5', title: 'Slightly Biased Toward Democrat' }, { from: 0.05, to: 0.10, color: '#99B7DE', title: 'Somewhat Biased Toward Democrat' }, { from: 0.10, to: 0.20, color: '#4C7FC2', title: 'More Biased Toward Democrat' }, { from: 0.20, to: 100, color: '#0049A8', title: 'Most Biased Toward Democrat' }];

//
// PAGE STARTUP / INIT FUNCTIONS
//

$(document).ready(function () {
    initYearPickers();
    initBoundaryPicker();
    initLoadStartingConditions(); // this will implicitly call loadDataForSelectedBoundaryAndYear() after setup, loading the map

    $(window).on('resize', handleResize);
    handleResize();
});

window.handleResize = function () {
    // various things that don't gracefully handle being resized, so we need to help them out
};

window.initYearPickers = function () {
    // a simple SELECT to choose a year, and trigger selectYear()

    var $picker_small = $('#yearpicker-small');
    PLAN_YEARS.slice().reverse().forEach(function (year) {
        $('<option></option>').text(year).prop('value', year).appendTo($picker_small);
    });
    $picker_small.change(function () {
        var year = $(this).val();
        selectYear(year);
    });
};

window.initBoundaryPicker = function () {
    $('#boundarypicker div').click(function () {
        var boundarytype = $(this).attr('data-boundary');
        selectBoundaryType(boundarytype);
    });
};

window.initLoadStartingConditions = function () {
    // analyze the #year-polytype hash to see what year + type we should load
    // provide some defaults
    var year = PLAN_YEARS[PLAN_YEARS.length - 1];
    var type = 'ushouse';

    var year_and_type = /^#(\d\d\d\d)\-(\w+)$/.exec(window.location.hash);
    if (year_and_type) {
        year = year_and_type[1];
        type = year_and_type[2];
    }

    // ready, set, go
    selectYear(year);
    selectBoundaryType(type);
};

//
// RUNTIME FUNCTIONS FOR CHANGING YEAR + DISTRICT TYPE
// loadDataForSelectedBoundaryAndYear() is the real worker here; the others are basically convenience functions
//

window.loadDataForSelectedBoundaryAndYear = function () {
    if (!CURRENT_VIEW.year || !CURRENT_VIEW.boundtype) return; // need both; during startup one will be blank, so avoid an error
    console.log(CURRENT_VIEW);

    // fetch the CSV file and then use the callbacks to update the map
    var url = '../data/bias_' + CURRENT_VIEW.boundtype + '.csv';
    Papa.parse(url, {
        download: true,
        header: true,
        complete: function complete(results) {
            // filter by the year (geography is implicit by which CSV was fetched)
            // and for each row assign the bias score to the state's row in the above
            // this is loop-within-loop as we match arrays to arrays, but P=50 and Q=20ish so it's affordable
            results = results.data.forEach(function (row) {
                //gda filter by state and year
            });

            //gda do something

            //gda do something
        }
    });

    // update URL params to show the current search
    // see also initLoadStartingConditions() which will load such a state
    var hash = '#' + CURRENT_VIEW.year + '-' + CURRENT_VIEW.boundtype;
    window.location.replace(hash);
};

window.selectYear = function (year) {
    // UI update: highlight this button
    $('#yearpicker-small').val(year);

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

/***/ }),

/***/ 49:
/***/ (function(module, exports) {

// removed by extract-text-webpack-plugin

/***/ })

/******/ });
//# sourceMappingURL=index.js.map