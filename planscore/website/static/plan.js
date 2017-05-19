function get_plan_url(url_pattern, id)
{
    return url_pattern.replace('{id}', id);
}

function load_plan_score(url, fields, table)
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
            for(var i in data.districts)
            {
                new_row = row.cloneNode(true);
                columns = new_row.getElementsByTagName('td');
                columns[0].innerText = i;
                for(var j = 0; j < fields.length; j++)
                {
                    columns[j+1].innerText = data.districts[i].totals[fields[j]];
                }
                tbody.appendChild(new_row);
            }
        }
    };

    request.onerror = function() { /* There was a connection error of some sort */ };
    request.send();
}
