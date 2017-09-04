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

function nice_gap(value)
{
    if(value > 0) {
        return '+' + (100 * value).toFixed(1) + '% for Democrats.';
    } else {
        return '+' + (100 * -value).toFixed(1) + '% for Republicans.';
    }
}

function clear_element(el)
{
    while(el.lastChild)
    {
        el.removeChild(el.lastChild);
    }
}

function which_score_summary(plan)
{
    var summaries = [
        'US House Efficiency Gap', 'Efficiency Gap',
        'SLDL Efficiency Gap', 'SLDU Efficiency Gap'
        ];
    
    for(var i = 0; i < summaries.length; i++)
    {
        var name = summaries[i];
        
        if(plan.summary[name] !== undefined)
        {
            return name;
        }
    }
}

function which_score_columns(plan)
{
    if(plan.summary['US House Efficiency Gap'] !== undefined)
    {
        return [
            'Population', 'Voting-Age Population', 'Black Voting-Age Population',
            'US House Dem Votes', 'US House Rep Votes'
        ];
    }
    
    if(plan.summary['Efficiency Gap'] !== undefined)
    {
        return ['Voters', 'Blue Votes', 'Red Votes'];
    }
    
    return [];
}

function load_plan_score(url, fields, table, score_EG)
{
    var request = new XMLHttpRequest();
    request.open('GET', url, true);
    
    function on_loaded_score(plan)
    {
        // Build list of columns
        var column = ['District'],
            columns = [column],
            field;
        
        for(var j = 0; j < plan.districts.length; j++)
        {
            column.push(j + 1);
        }
        
        for(var i in fields)
        {
            field = fields[i];
            column = [field];
            columns.push(column);
            
            for(var j in plan.districts)
            {
                column.push(plan.districts[j].totals[field]);
            }
        }
        
        // Remove any column that doesn't belong
        var column_names = which_score_columns(plan);
        
        for(var i = columns.length - 1; i > 0; i--)
        {
            if(column_names.indexOf(columns[i][0]) === -1)
            {
                columns.splice(i, 1);
            }
        }
        
        // Write table out to page
        var new_row = document.createElement('tr'),
            new_cell;
        
        for(var i in columns)
        {
            new_cell = document.createElement('th');
            new_cell.innerText = columns[i][0];
            new_row.appendChild(new_cell);
        }
        
        table.appendChild(new_row);
        
        for(var j = 1; j < columns[0].length; j++)
        {
            new_row = document.createElement('tr');
            new_cell = document.createElement('td');
            new_cell.innerText = columns[0][j];
            new_row.appendChild(new_cell);
        
            for(var i = 1; i < columns.length; i++)
            {
                new_cell = document.createElement('td');
                new_cell.innerText = nice_count(columns[i][j]);
                new_row.appendChild(new_cell);
            }
        
            table.appendChild(new_row);
        }
        
        // Populate efficiency gap score.
        var summary_name = which_score_summary(plan);
        clear_element(score_EG);
    
        var new_h3 = document.createElement('h3'),
            new_score = document.createElement('p'),
            new_words = document.createElement('p');
    
        new_h3.innerText = 'Efficiency Gap';
        new_score.className = 'score'

        if(Math.abs(plan.summary[summary_name]) < .07) {
            new_score.innerText = 'A';
        } else {
            new_score.innerText = 'F';
        }

        new_words.innerText = nice_gap(plan.summary[summary_name]);
    
        score_EG.appendChild(new_h3);
        score_EG.appendChild(new_score);
        score_EG.appendChild(new_words);
    }

    request.onload = function()
    {
        if(request.status >= 200 && request.status < 400)
        {
            // Returns a dictionary with a list of districts
            var data = JSON.parse(request.responseText);
            console.log('Loaded plan:', data);
            on_loaded_score(data);
        }
    };

    request.onerror = function() { /* There was a connection error of some sort */ };
    request.send();
}

function load_plan_map(url, div, color)
{
    var request = new XMLHttpRequest();
    request.open('GET', url, true);

    function on_loaded_geojson(data)
    {
        var geojson = L.geoJSON(data, {
            style: { color: color, weight: 1, fillOpacity: .1 }
            });
    
        console.log('GeoJSON bounds:', geojson.getBounds());

        // Initialize the map on the passed div in the middle of the ocean
        var map = L.map(div, {
            scrollWheelZoom: false,
            center: [0, 0],
            zoom: 8
        });
        
        var pane = map.createPane('labels');
        pane.style.zIndex = 450; // http://leafletjs.com/reference-1.0.3.html#map-overlaypane
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
        L.tileLayer('http://{s}.tile.stamen.com/toner-labels/{z}/{x}/{y}{r}.png', {
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