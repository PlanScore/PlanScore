function fetch_upload_tokens(url, form, signal) 
{
    return fetch(url, {signal}).then(r => r.json()).then(data => {
        // Returns a two-element array with URL and form fields.
        const form_action_url = data[0];
        const upload_fields = data[1];

        for(var key in upload_fields) {
            form.elements[key].value = upload_fields[key];
        }
        form.action = form_action_url;
        console.log('Upload tokens populated.');
    });
}
