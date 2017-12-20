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
/******/ 	return __webpack_require__(__webpack_require__.s = 109);
/******/ })
/************************************************************************/
/******/ ({

/***/ 109:
/***/ (function(module, exports, __webpack_require__) {

"use strict";


// this page's HTML template with the [hash] cache-buster
// and the only stylesheet
__webpack_require__(3);
__webpack_require__(56);

// polyfills
//require('core-js/fn/array/includes');

// bundle some local/vendor libraries
//require('./js/leaflet-control-basemapbar.js');
//require('./js/leaflet-control-basemapbar.css');


//
// CONSTANTS
//

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

    $(window).on('resize', handleResize);
    handleResize();
});

window.handleResize = function () {
    // various things that don't gracefully handle being resized, so we need to help them out
};

/***/ }),

/***/ 3:
/***/ (function(module, exports) {

// removed by extract-text-webpack-plugin

/***/ }),

/***/ 56:
/***/ (function(module, exports, __webpack_require__) {

module.exports = __webpack_require__.p + "arizona/index.html";

/***/ })

/******/ });
//# sourceMappingURL=index.js.map