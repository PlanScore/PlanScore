# PlanScore Front-Facing Website

Totally separate from the back-end code, this is the public-facing website. This is run from thre `gh-pages` branch of the `PlanScore/PlanScore` repository.

## Site URL

https://planscore.github.io/PlanScore/home/



## Data CSVs

The datasets which power the site, are under the `data/` folder.

Data dictionary for bias CSVs: https://docs.google.com/spreadsheets/d/1eMwwL8eaxD3aAyiy410yt79Cik2GV31WrXWyzFsiSTs/edit#gid=1340292617


## Development and Code Layout

Babel, SASS/SCSS, Webpack.

Upon initial setup on your system, run `nvm use` and `yarn install` to set up build tools.

`npm run serve` will run a HTTP server where you may see your edits. This will automagically reload when files are changed. This webserver runs on **http://localhost:8000***

Each page is its own folder, and your edits would be made to each folder's **index.src.html** **index.scss** **index.js6** *Note that the individual states are special; see below.*


### The State Pages Are Special

**Do not edit the `index.*` files for the 50 states.** There are 50 directories and thus pages for Alabama, Alaska, ... etc. But we do not maintain 50 separate **index.js6** **index.scss** **index.src.html** files!

Instead, you'll want to make edits to the `_statetemplate` files (**state_template.js6**, **state_template.scss**, **state_template.src.html**). Then run `npm run states` to copy these template files into the 50 target folders.

If you are running *webpack-dev-server*, it will automagically detect the files having changed, and will trigger a rebuild and reload as usual. Note that this takes a moment; be patient.

While working within the `_statetemplate/` content, some notes of interest:
* **state_template.src.html** -- You may insert the phrase **STATE_NAME** into the HTML. When the template is copied into the state folder, this will be replaced with the state's Properly Capitalized Name.
* All states will receive exactly the same programming, stylesheet, and HTML template (except for the STATE_NAME tag), so they should "detect" their state based on the URL string, if they will need to filter data or otherwise configure custom behavior.


###Static Content

The `WEBSITE_OUTPUT/` directory is where the compiled website output will be placed (see Deployment section).

It is also where "truly static" files are hosted, e.g. the `data/` and `images/` folders, which are needed by the live site and which also are served from webpack-dev-server.

For more details, see this folder's `.gitignore` file, and the Deployment section of this document.


### Shared Content / Partial Views

Some content is shared between pages, such as the sitewide navbar, the footer, and some of the HTML HEAD content. These are called "partial views".

To use them in the HTML templates, simply use the following tags. They will be substituted when `npm run build` is done, or when the webpack-dev-server is restarted.
```
<!--[include_headtags]-->
<!--[include_navbar]-->
<!--[include_footer]-->
```

Note that *webpack-dev-server* will not reload these when they are modified. If you are making changes to these common elements, you will need to stop and restart the *webpack-dev-server*.

If you need to define some new partial views, the following will be useful:
* These are defined in the `htmlpartials/` folder. Each one defines a JavaScript variable containing a block of HTML, e.g. the navbar.
* The `webpack.config.js` defines **HTML_PARTIALS** by loading those files.
* The `webpack.config.js` then uses **StringReplacePlugin** to perform the above-mentioned substitutions, e.g. `<!--[include_footer]-->` as the `.src.html` templates are processed.


## Deployment

Running `npm run build` will compile the js6/scss/src.html files for all of the subfolders, and will place their respective outputs into the `WEBSITE_OUTPUT/` directory.

The result is:
* A set of folders for each page + state, with each folder containing the CSS/JS/HTML files for the page.
  * These build artifacts are not in version control.
* The `data/` and `images/` folders of static content.
  * These were there all along, and are in version control.
* The `index.html` file which redirects visitors from **/** to **/home/** when they land on the site.
  * This was there all along, and is in version control.
