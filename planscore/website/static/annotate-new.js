function format_url(url_pattern, id)
{
    return url_pattern.replace('{id}', id);
}

// Copied from https://davidwalsh.name/query-string-javascript
function getUrlParameter(name, search)
{
    name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
    var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    var results = regex.exec(search);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
}

function show_message(text, preread_section, message_section)
{
    while(message_section.firstChild)
    {
        message_section.removeChild(message_section.firstChild);
    }

    message_section.appendChild(document.createElement('p'));
    message_section.firstChild.appendChild(document.createTextNode(text));

    preread_section.style.display = 'none';
    message_section.style.display = 'block';
}

function hide_message(preread_section, message_section)
{
    preread_section.style.display = 'block';
    message_section.style.display = 'none';
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

function which_plan_districts_count(plan)
{
    if(typeof plan.districts == 'object' && plan.districts.length !== undefined)
    {
        return plan.districts.length;
    }

    return null;
}

function get_description(plan, modified_at)
{
    var states = {
        'XX': 'Null Island',
        'AL': 'Alabama', 'NE': 'Nebraska', 'AK': 'Alaska', 'NV': 'Nevada',
        'AZ': 'Arizona', 'NH': 'New Hampshire', 'AR': 'Arkansas',
        'NJ': 'New Jersey', 'CA': 'California', 'NM': 'New Mexico',
        'CO': 'Colorado', 'NY': 'New York', 'CT': 'Connecticut',
        'NC': 'North Carolina', 'DE': 'Delaware', 'ND': 'North Dakota',
        'DC': 'District of Columbia', 'OH': 'Ohio', 'FL': 'Florida',
        'OK': 'Oklahoma', 'GA': 'Georgia', 'OR': 'Oregon', 'HI': 'Hawaii',
        'PA': 'Pennsylvania', 'ID': 'Idaho', 'PR': 'Puerto Rico',
        'IL': 'Illinois', 'RI': 'Rhode Island', 'IN': 'Indiana',
        'SC': 'South Carolina', 'IA': 'Iowa', 'SD': 'South Dakota',
        'KS': 'Kansas', 'TN': 'Tennessee', 'KY': 'Kentucky', 'TX': 'Texas',
        'LA': 'Louisiana', 'UT': 'Utah', 'ME': 'Maine', 'VT': 'Vermont',
        'MD': 'Maryland', 'VA': 'Virginia', 'MA': 'Massachusetts',
        'VI': 'Virgin Islands', 'MI': 'Michigan', 'WA': 'Washington',
        'MN': 'Minnesota', 'WV': 'West Virginia', 'MS': 'Mississippi',
        'WI': 'Wisconsin', 'MO': 'Missouri', 'WY': 'Wyoming',
        'MT': 'Montana'
        };
    
    var description = ['Plan uploaded'], houses = {'ushouse': 'U.S. House',
        'statesenate': 'State Senate', 'statehouse': 'State House'};
    
    if(plan['start_time'])
    {
        modified_at = new Date(plan.start_time * 1000);
    }
    
    if(plan['model'])
    {
        description = [states[plan.model.state],
            houses[plan.model.house], 'plan uploaded'].join(' ');
    }

    return (date_age(modified_at) > 86400)
            ? [description, 'on', modified_at.toLocaleDateString()].join(' ')
            : [description, 'at', modified_at.toLocaleString()].join(' ');
}

function load_plan_preread(url, message_section, preread_section, description,
    incumbency_unavailable, incumbency_scenarios, first_incumbent_row)
{
    var request = new XMLHttpRequest();
    request.open('GET', url, true);

    show_message('Loading district plan…', preread_section, message_section);

    function on_loaded_preread(plan, modified_at)
    {
        if(!which_plan_districts_count(plan)) {
            show_message(plan['message'] ? plan.message : 'District plan failed to load.',
                preread_section, message_section);
            return;

        } else {
            hide_message(preread_section, message_section);
        }

        // Clear out and repopulate description.
        clear_element(description);
        description.appendChild(document.createElement('i'));
        description.lastChild.appendChild(
            document.createTextNode(get_description(plan, modified_at)));
        
        if(!plan.model.incumbency)
        {
            incumbency_unavailable.style.display = 'block';
            incumbency_scenarios.style.display = 'none';
        }
        
        var table_body = first_incumbent_row.parentNode,
            template_row = table_body.removeChild(first_incumbent_row);
        
        for(var i = 0; i < plan.districts.length; i++)
        {
            var new_row = template_row.cloneNode(true),
                row_cells = new_row.getElementsByTagName('TD'),
                row_inputs = new_row.getElementsByTagName('INPUT');
            
            row_cells[0].innerHTML = i + 1;
            row_inputs[0].name = 'incumbent-' + (i + 1);
            row_inputs[1].name = 'incumbent-' + (i + 1);
            row_inputs[2].name = 'incumbent-' + (i + 1);
            
            table_body.appendChild(new_row);
            row_inputs[1].checked = true;
        }
    }

    request.onload = function()
    {
        if(request.status >= 200 && request.status < 400)
        {
            // Returns a dictionary with a list of districts
            var data = JSON.parse(request.responseText),
                modified_at = new Date(request.getResponseHeader('Last-Modified'));
            console.log('Loaded plan:', data);
            on_loaded_preread(data, modified_at);
            return;
        }
        
        show_message('The district plan failed to load.', preread_section, message_section);
    };

    request.onerror = function() { /* There was a connection error of some sort */ };
    request.send();
}

// Export functions for testing
if(typeof module !== 'undefined' && module.exports)
{
    module.exports = {
        format_url: format_url, getUrlParameter: getUrlParameter,
        which_plan_districts_count: which_plan_districts_count,
        get_description: get_description, date_age: date_age
        };
}
