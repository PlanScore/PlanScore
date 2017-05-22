function format_url(url_pattern, id)
{
    return url_pattern.replace('{id}', id);
}

function nice_count(value)
{
    if(value >= 100) {
        return value.toFixed(0);
    } else if(value >= 10) {
        return value.toFixed(1);
    } else {
        return value.toFixed(2);
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

function load_plan_score(url, fields, table, eff_gap)
{
    var request = new XMLHttpRequest();
    request.open('GET', url, true);

    request.onload = function()
    {
        if(request.status >= 200 && request.status < 400)
        {
            // Returns a dictionary with a list of districts
            var data = JSON.parse(request.responseText);
            console.log('loaded', data);
            
            var rows = document.getElementsByTagName('tr'),
                row = rows[rows.length - 1],
                tbody = row.parentNode,
                columns;
            
            // Remove the sample row
            tbody.removeChild(row);
            
            // Clone it for each district
            for(var i = 0; i < data.districts.length; i++)
            {
                new_row = row.cloneNode(true);
                columns = new_row.getElementsByTagName('td');
                columns[0].innerText = i + 1;
                for(var j = 0; j < fields.length; j++)
                {
                    columns[j+1].innerText = nice_count(data.districts[i].totals[fields[j]]);
                }
                tbody.appendChild(new_row);
            }
            
            // Note the efficiency gap
            eff_gap.innerText = nice_gap(data['summary']['Efficiency Gap']);
        }
    };

    request.onerror = function() { /* There was a connection error of some sort */ };
    request.send();
}
