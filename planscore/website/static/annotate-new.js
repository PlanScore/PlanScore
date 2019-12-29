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

function load_plan_preread(url, message_section, preread_section, first_incumbent_row)
{
    var request = new XMLHttpRequest();
    request.open('GET', url, true);

    show_message('Loading district plan…', preread_section, message_section);

    function on_loaded_preread(plan, modified_at)
    {
        hide_message(preread_section, message_section);
        
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
            row_inputs[0].disabled = true;
            row_inputs[1].checked = true;
            row_inputs[2].disabled = true;
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
        format_url: format_url, getUrlParameter: getUrlParameter
        };
}
