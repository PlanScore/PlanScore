# PlanScore Front-Facing Website

Totally separate from the back-end code, this is the public-facing website.

## Site URL

https://planscore.org/



## Data CSVs

The datasets which power the site, are under the `WEBSITE_OUTPUT/data/` folder. Most of `WEBSITE_OUTPUT` is gitignored, with the exception of this folder and static images.

Data dictionary for bias CSVs: https://docs.google.com/spreadsheets/d/1aBffpd3Fv0tCvz6waMk2fGhyV3ZfSSUaWyJKrzi-HL8/edit#gid=1340292617


## Quick Build

1.  Use Docker to cover for Mac/Linux case-sensitive `sed`, with Circle CI image matching Node version used in test/deploy script:
    
        docker pull circleci/node:8.2

2.  Install required Node packages:
    
        docker run --rm -it -v `pwd`:/vol -w /vol circleci/node:8.2 yarn install

3.  Build content of `WEBSITE_OUTPUT` and serve it locally at http://0.0.0.0:8000 (this step may take time to build):
    
        docker run --rm -it -v `pwd`:/vol -w /vol -p 8000:8000 circleci/node:8.2 npm run serve

4.  Update raw data in `WEBSITE_OUTPUT/data` directory.


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
* **state_template.src.html** -- You may insert the phrase **STATE_NAME** into the HTML. When the template is copied into the state folder, this will be replaced with the state's Properly Capitalized Name. **STATE_SLUG** in the HTML will be replaced with the URL-friendly name of the state, which is useful for per-state references like OpenGraph images.
* All states will receive exactly the same programming, stylesheet, and HTML template (except for the STATE_NAME tag), so they should "detect" their state based on the URL string, if they will need to filter data or otherwise configure custom behavior.

**NOTE FOR MAC USERS**
If you run `npm run states` out of the box without making a single change to the code, you may see git changes with all your user-visible state names showing as lowercase. This breaks the site since data keys are assuming proper capitalization of state names. The cause is that the `sed` REGEX commands in `npm run states` rely on GNU utilities that are not present in MacOS's default BSD version of `sed`. Here's [some info on that](https://unix.stackexchange.com/questions/13711/differences-between-sed-on-mac-osx-and-other-standard-sed). You can solve the issue by installing `gnu-sed` as outlined in [this StackOverflow post](https://stackoverflow.com/questions/30003570/how-to-use-gnu-sed-on-mac-os-x). If you do `npm run states` after that install and before making changes, you should see no uncommitted changes in your repo, which is expected. Now you can edit the template files and do `npm run states` and see only the changes you meant to make.

### Static Content

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


## Adding New Pages To The Site

To add a new page to the site:
* Copy the `_pagestarter` folder as your new page-folder, e.g. `cp -rp _pagestarter/ voting/`
* List the new folder's `index.js6` file in the `webpack.config.js` file.
  * If you are using webpack-dev-server, you will need to restart it for it pick up the newly-listed page-folder.
* Get hacking on the three files, as described in the Development section. Fill in HTML content, JavaScript code, and page-specific SCSS.
