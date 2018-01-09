// custom zoom bar control that includes the Zoom Home function in addition to the + and - to zoom in and out
// external dependency: this has a glyphicon class so does require Bootstrap glyphicons in order to look right
L.Control.PartyLegend = L.Control.extend({
    options: {
        position: 'topright',
    },

    initialize: function(options) {
        L.Util.setOptions(this, options);
    },

    onAdd: function (map) {
        var container = L.DomUtil.create('div', 'planscore-partylegend');

        var row_d    = L.DomUtil.create('div', 'planscore-partylegend-legend', container);
        var swatch_d = L.DomUtil.create('div', 'planscore-partylegend-swatch planscore-partylegend-swatch-democrat', row_d);
        var words_d  = L.DomUtil.create('div', 'planscore-partylegend-words', row_d);
        words_d.innerHTML = 'Always Democrat';

        var row_r    = L.DomUtil.create('div', 'planscore-partylegend-legend', container);
        var swatch_r = L.DomUtil.create('div', 'planscore-partylegend-swatch planscore-partylegend-swatch-republican', row_r);
        var words_r  = L.DomUtil.create('div', 'planscore-partylegend-words', row_r);
        words_r.innerHTML = 'Always Republican';

        var row_x    = L.DomUtil.create('div', 'planscore-partylegend-legend', container);
        var swatch_x = L.DomUtil.create('div', 'planscore-partylegend-swatch planscore-partylegend-swatch-both', row_x);
        var words_x  = L.DomUtil.create('div', 'planscore-partylegend-words', row_x);
        words_x.innerHTML = 'Mixed Results';

        return container;
    },
});
