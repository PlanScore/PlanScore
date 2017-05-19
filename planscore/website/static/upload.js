function enable_form(url, form)
{
    var request = new XMLHttpRequest();
    request.open('GET', url, true);

    request.onload = function()
    {
        if(request.status >= 200 && request.status < 400)
        {
            // Returns a two-element array with URL and form fields.
            var data = JSON.parse(request.responseText);
            for(var key in data[1]) {
                form.elements[key].value = data[1][key];
            }
            form.action = data[0];
            form.elements['submission'].disabled = false;
        }
    };

    request.onerror = function() { /* There was a connection error of some sort */ };
    request.send();
}
