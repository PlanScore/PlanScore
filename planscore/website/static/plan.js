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
        return '+' + (100 * value).toFixed(1) + '% for Blue';
    } else {
        return '+' + (100 * -value).toFixed(1) + '% for Red';
    }
}

function load_plan_score(url, fields, table, eff_gaps)
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
        
        // Remove any column with empty rows
        for(var i = columns.length - 1; i > 0; i--)
        {
            for(var j = 1; j <= plan.districts.length; j++)
            {
                if(columns[i][j] == undefined)
                {
                    columns.splice(i, 1);
                    break;
                }
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
        
        // Note the efficiency gaps
        var new_term, new_defn;
        
        for(var name in plan.summary)
        {
            if(plan.summary[name] == undefined)
            {
                continue;
            }
        
            new_term = document.createElement('dt');
            new_defn = document.createElement('dd');
            new_term.innerText = name;
            new_defn.innerText = nice_gap(plan.summary[name]);
            new_term.appendChild(new_defn);
            eff_gaps.appendChild(new_term);
        }
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
    
        // Add Toner tiles for base map
        L.tileLayer('http://{s}.tile.stamen.com/toner-lite/{z}/{x}/{y}@2x.png', {
            attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://maps.stamen.com/">Map tiles</a> by <a href="http://stamen.com/">Stamen</a>',
            maxZoom: 18
        }).addTo(map);
        
        // Add a GeoJSON layer and fit it into view
        geojson.addTo(map);
        map.fitBounds(geojson.getBounds());
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