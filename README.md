# PlanScore Front-Facing Website

Totally separate from the back-end code, this is the public-facing website. This is run from thre `gh-pages` branch of the `PlanScore/PlanScore` repository.

## Site URL

https://planscore.github.io/PlanScore/home/


## Development and Code Layout

Babel, SASS/SCSS, Webpack.

Upon initial setup on your system, run `nvm use` and `yarn install` to set up build tools.

Each page is its own folder, so this may be served as static files without special webserver configuration.

Your edits would be made to each folder's **index.src.html** **index.scss** **index.js6**

Running `npm run build` will compile the browser-consumable files **index.html** **index.css** **index.js** within each folder. Note that these outputs **are** included in version control, so they may be hosted via Github Pages without us needing to work in additional tooling.

`npm run serve` will run a HTTP server, as well as watching and rebuilding (below).


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


### Deployment

This is run from the `gh-pages` branch of the `PlanScore/PlanScore` repository.

Be sure you are using the `gh-pages` branch.

After running the `npm run build`, commit the new built files into a new commit, and then push. This will cause the GH Pages site to be updated. (though it can take a few minutes)
