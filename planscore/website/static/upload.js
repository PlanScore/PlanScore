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
            const form_action_url = data[0];
            const upload_fields = data[1];

            for(var key in upload_fields) {
                form.elements[key].value = upload_fields[key];
            }
            form.action = form_action_url;
            form.dataset.configured = "true"
        }
    };

    request.onerror = function(e) { 
        console.error('There was a connection error', e);
    };
    request.send();
}
