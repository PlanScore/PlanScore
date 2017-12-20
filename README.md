## PlanScore Front-Facing Website

Totally separate from the back-end code, this is the public-facing website. This is run from thre `gh-pages` branch of the `PlanScore/PlanScore` repository.

### Site URL

htt://www.planscore.org/


### Development and Code Layout

Babel, SASS/SCSS, Webpack.

Upon initial setup on your system, run `nvm use` and `yarn install` to set up build tools.

Each page is its own folder, so this may be served as static files without special webserver configuration.

Your edits would be made to each folder's **index.src.html** **index.scss** **index.js6**

Running `npm run build` will compile the browser-consumable files **index.html** **index.css** **index.js** within each folder. Note that these outputs **are** included in version control, so they may be hosted via Github Pages without us needing to work in additional tooling.

`npm run serve` will run a HTTP server, as well as watching and rebuilding (below).

`npm run watch` will watch for changes and re-run `npm run build` upon detecting changes.

Deployment: This is run from the `gh-pages` branch of the `PlanScore/PlanScore` repository. Simply commiting the new built files, and then pushing, will cause the GH Pages site to be updated. (though it can take a few minutes)
