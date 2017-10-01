function format_url(url_pattern, id)
{
    return url_pattern.replace('{id}', id);
}

function nice_count(value)
{
    if(value >= 1000) {
        return (value / 1000).toFixed(1) + 'k';
    } else if(value >= 100) {
        return value.toFixed(0);
    } else if(value >= 10) {
        return value.toFixed(1);
    } else if(value >= 0) {
        return value.toFixed(2);
    } else {
        return '–';
    }
}

function nice_percent(value)
{
    return (100 * value).toFixed(1) + '%';
}

function nice_gap(value)
{
    if(value > 0) {
        return '+' + nice_percent(value) + ' for Democrats';
    } else {
        return '+' + nice_percent(-value) + ' for Republicans';
    }
}

function clear_element(el)
{
    while(el.lastChild)
    {
        el.removeChild(el.lastChild);
    }
}

function date_age(date)
{
    return (new Date()).getTime() / 1000 - date.getTime() / 1000;
}

function which_score_summary_name(plan)
{
    var summaries = [
        'US House Efficiency Gap', 'Efficiency Gap',
        'SLDL Efficiency Gap', 'SLDU Efficiency Gap'
        ];
    
    for(var i = 0; i < summaries.length; i++)
    {
        var name = summaries[i];
        
        if(typeof plan.summary[name] === 'number')
        {
            return name;
        }
    }
    
    return null;
}

function which_score_column_names(plan)
{
    if(typeof plan.summary['US House Efficiency Gap'] === 'number')
    {
        return [
            'Population', 'Voting-Age Population', 'Black Voting-Age Population',
            'US House Dem Votes', 'US House Rep Votes'
        ];
    }
    
    if(typeof plan.summary['Efficiency Gap'] === 'number')
    {
        return ['Voters', 'Blue Votes', 'Red Votes'];
    }
    
    return [];
}

function which_district_color(district, plan)
{
    var totals = district.totals,
        color_red = '#D45557',
        color_blue = '#4D90D1';
    
    if(typeof plan.summary['US House Efficiency Gap'] === 'number')
    {
        if(totals['US House Dem Votes'] > totals['US House Rep Votes']) {
            return color_blue;
        } else {
            return color_red;
        }
    }

    if(typeof plan.summary['Efficiency Gap'] === 'number')
    {
        if(totals['Blue Votes'] > totals['Red Votes']) {
            return color_blue;
        } else {
            return color_red;
        }
    }
    
    // neutral gray
    return '#808080';
}

function show_efficiency_gap_score(plan, score_EG)
{
    var summary_name = which_score_summary_name(plan);
    clear_element(score_EG);

    var new_h3 = document.createElement('h3'),
        new_score = document.createElement('p'),
        new_words = document.createElement('p');

    new_h3.innerText = 'Efficiency Gap';
    new_score.className = 'score'

    if(Math.abs(plan.summary[summary_name]) < .02) {
        new_score.innerText = 'A';
        new_words.innerText = (nice_gap(plan.summary[summary_name])
            + ' is close to zero.');
    } else if(Math.abs(plan.summary[summary_name]) < .04) {
        new_score.innerText = 'B';
        new_words.innerText = (nice_gap(plan.summary[summary_name])
            + ' is well within 7% threshold.');
    } else if(Math.abs(plan.summary[summary_name]) < .07) {
        new_score.innerText = 'C';
        new_words.innerText = (nice_gap(plan.summary[summary_name])
            + ' is within 7% threshold.');
    } else if(Math.abs(plan.summary[summary_name]) < .09) {
        new_score.innerText = 'D';
        new_words.innerText = (nice_gap(plan.summary[summary_name])
            + ' is outside 7% threshold.');
    } else {
        new_score.innerText = 'F';
        new_words.innerText = (nice_gap(plan.summary[summary_name])
            + ' is far outside 7% threshold.');
    }

    score_EG.appendChild(new_h3);
    score_EG.appendChild(new_score);
    score_EG.appendChild(new_words);
}

function show_population_score(plan, score_pop)
{
    var summary_name = which_score_summary_name(plan);

    var populations = [];
    
    for(var i = 0; i < plan.districts.length; i++)
    {
        var totals = plan.districts[i].totals;
        console.log(totals);
        if(summary_name == 'Efficiency Gap') {
            populations.push(totals['Voters']);
        } else if(summary_name == 'US House Efficiency Gap') {
            populations.push(totals['Population']);
        } else {
            return;
        }
    }
    
    var max_pop = Math.max.apply(null, populations),
        min_pop = Math.min.apply(null, populations);
    
    clear_element(score_pop);

    var new_h3 = document.createElement('h3'),
        new_score = document.createElement('p'),
        new_words = document.createElement('p');

    new_h3.innerText = 'Population';
    new_score.className = 'score'

    if(max_pop / min_pop < 1.02) {
        new_score.innerText = 'A';
    } else {
        new_score.innerText = 'F';
    }

    new_words.innerText = ('Largest district has ' 
        + nice_percent(max_pop / min_pop - 1)
        + ' greater population than smallest district.');

    score_pop.appendChild(new_h3);
    score_pop.appendChild(new_score);
    score_pop.appendChild(new_words);
}

function show_demographics_score(plan, score_dem)
{
    var summary_name = which_score_summary_name(plan);

    if(summary_name == 'Efficiency Gap')
    {
        return;
    }
    
    var black_shares = [];
    
    for(var i = 0; i < plan.districts.length; i++)
    {
        var totals = plan.districts[i].totals;
        black_shares.push(totals['Black Voting-Age Population'] / totals['Voting-Age Population']);
    }
    
    clear_element(score_dem);

    var new_h3 = document.createElement('h3'),
        new_score = document.createElement('p'),
        new_words = document.createElement('p');

    new_h3.innerText = 'Demographics';
    new_score.className = 'score'

    if(Math.max.apply(null, black_shares) > .33) {
        new_score.innerText = 'A';
    } else {
        new_score.innerText = 'F';
    }

    new_words.innerText = ('One district with ' 
        + nice_percent(Math.max.apply(null, black_shares)) + ' minority population');

    score_dem.appendChild(new_h3);
    score_dem.appendChild(new_score);
    score_dem.appendChild(new_words);
}

function show_message(text, score_section, message_section)
{
    while(message_section.firstChild)
    {
        message_section.removeChild(message_section.firstChild);
    }
    
    message_section.appendChild(document.createElement('p'));
    message_section.firstChild.appendChild(document.createTextNode(text));

    score_section.style.display = 'none';
    message_section.style.display = 'block';
}

function hide_message(score_section, message_section)
{
    score_section.style.display = 'block';
    message_section.style.display = 'none';
}

function load_plan_score(url, fields, message_section, score_section,
    description, table, score_EG, score_pop, score_dem, map_url, map_div)
{
    var request = new XMLHttpRequest();
    request.open('GET', url, true);
    
    show_message('Loading district plan…', score_section, message_section);

    function on_loaded_score(plan, modified_at)
    {
        if(which_score_summary_name(plan) === null) {
            show_message('District plan failed to load.', score_section, message_section);
            return;

        } else {
            hide_message(score_section, message_section);
        }
        
        // Clear out and repopulation description.
        clear_element(description);
        
        description.innerHTML = 'Nar nar nar';

        description.appendChild(document.createElement('br'));
        description.appendChild(document.createElement('i'));
        description.lastChild.appendChild(document.createTextNode(
            (date_age(modified_at) > 86400)
                ? 'Uploaded on '+ modified_at.toLocaleDateString()
                : 'Uploaded at '+ modified_at.toLocaleString()));
        
        // Build list of columns
        var current_column = ['District'],
            all_columns = [current_column],
            field;
        
        for(var j = 0; j < plan.districts.length; j++)
        {
            current_column.push(j + 1);
        }
        
        for(var i in fields)
        {
            field = fields[i];
            current_column = [field];
            all_columns.push(current_column);
            
            for(var j in plan.districts)
            {
                current_column.push(plan.districts[j].totals[field]);
            }
        }
        
        // Remove any column that doesn't belong
        var column_names = which_score_column_names(plan);
        
        for(var i = all_columns.length - 1; i > 0; i--)
        {
            if(column_names.indexOf(all_columns[i][0]) === -1)
            {
                all_columns.splice(i, 1);
            }
        }
        
        // Write table out to page
        var new_row = document.createElement('tr'),
            new_cell;
        
        for(var i in all_columns)
        {
            new_cell = document.createElement('th');
            new_cell.innerText = all_columns[i][0];
            new_row.appendChild(new_cell);
        }
        
        table.appendChild(new_row);
        
        for(var j = 1; j < all_columns[0].length; j++)
        {
            new_row = document.createElement('tr');
            new_cell = document.createElement('td');
            new_cell.innerText = all_columns[0][j];
            new_row.appendChild(new_cell);
        
            for(var i = 1; i < all_columns.length; i++)
            {
                new_cell = document.createElement('td');
                new_cell.innerText = nice_count(all_columns[i][j]);
                new_row.appendChild(new_cell);
            }
        
            table.appendChild(new_row);
        }
        
        // Populate scores.
        show_efficiency_gap_score(plan, score_EG);
        show_population_score(plan, score_pop);
        show_demographics_score(plan, score_dem);
        
        // Go on to load the map.
        load_plan_map(map_url, map_div, plan);
    }

    request.onload = function()
    {
        if(request.status >= 200 && request.status < 400)
        {
            // Returns a dictionary with a list of districts
            var data = JSON.parse(request.responseText),
                modified_at = new Date(request.getResponseHeader('Last-Modified'));
            console.log('Loaded plan:', data);
            on_loaded_score(data, modified_at);
        }
    };

    request.onerror = function() { /* There was a connection error of some sort */ };
    request.send();
}

function load_plan_map(url, div, plan)
{
    var request = new XMLHttpRequest();
    request.open('GET', url, true);

    function on_loaded_geojson(data)
    {
        var geojson = L.geoJSON(data, {
            style: function(feature)
            {
                var district = plan.districts[data.features.indexOf(feature)];
                return { weight: 2, fillOpacity: .5, color: which_district_color(district, plan) };
            }
            });
    
        console.log('GeoJSON bounds:', geojson.getBounds());

        // Initialize the map on the passed div in the middle of the ocean
        var map = L.map(div, {
            scrollWheelZoom: false,
            center: [0, 0],
            zoom: 8
        });
        
        var pane = map.createPane('labels');
        pane.style.zIndex = 650; // http://leafletjs.com/examples/map-panes/
        pane.style.pointerEvents = 'none';
    
        // Add Toner tiles for base map
        L.tileLayer('https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_nolabels/{z}/{x}/{y}{r}.png', {
            attribution: '&copy;<a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>, &copy;<a href="https://carto.com/attribution">CARTO</a>',
            maxZoom: 18
        }).addTo(map);
        
        // Add a GeoJSON layer and fit it into view
        geojson.addTo(map);
        map.fitBounds(geojson.getBounds());

        // Add Toner label tiles for base map
        L.tileLayer('https://stamen-tiles.a.ssl.fastly.net/toner-labels/{z}/{x}/{y}{r}.png', {
            attribution: '&copy;<a href="http://stamen.com/">Stamen</a>',
            pane: 'labels',
            maxZoom: 18
        }).addTo(map);
    }

    request.onload = function()
    {
        if(request.status >= 200 && request.status < 400)
        {
            // Returns a GeoJSON dictionary
            var data = JSON.parse(request.responseText);
            console.log('Loaded map:', data);
            on_loaded_geojson(data);
        }
    };

    request.onerror = function() { /* There was a connection error of some sort */ };
    request.send();
}

// Export functions for testing
if(module !== undefined)
{
    module.exports = {
        format_url: format_url, nice_count: nice_count,
        nice_percent: nice_percent, nice_gap: nice_gap, date_age: date_age,
        which_score_summary_name: which_score_summary_name,
        which_score_column_names: which_score_column_names,
        which_district_color: which_district_color
        };
}
