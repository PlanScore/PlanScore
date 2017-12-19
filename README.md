## PlanScore Front-Facing Website

Totally separate from the back-end code, this is the public-facing website. This is run from thre `gh-pages` branch of the `PlanScore/PlanScore` repository.

### Site URL

htt://www.planscore.org/


### Development

Babel, SASS/SCSS, Webpack.

Upon initial setup on your system, run `nvm use` and `yarn install` to set up build tools.

Your edits would be made to **index.src.html** **index.scss** **index.js6**

Running `npm run build` will compile the browser-consumable files **index.html** **index.css** **index.js** Note that these outputs **are** included in version control, so they may be hosted via Github Pages without us needing to work in additional tooling.

`npm run serve` will run a HTTP server, as well as watching and rebuilding (below).

`npm run watch` will watch for changes and re-run `npm rin build` upon detecting changes.

Deployment: This is run from thre `gh-pages` branch of the `PlanScore/PlanScore` repository. Simply commiting the new built files, and then pushing, will cause the GH Pages site to be updated. (though it can take a few minutes)
