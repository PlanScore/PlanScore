/*
 * Webpack configuration and build scripts for use with Django applications
 * Version 1, July 2017
 * Greg "Gregor" Allensworth, GreenInfo Network   gregor@greeninfo.org
 *
 * Basic usage:
 * - yarn install -- Initial setup of dependencies for build/watch tasks
 * - npm run build -- Analyze files, generate output files.
 * - npm run watch -- Watches for file changes, recompiles as needed.
 *
 * Design goals:
 *
 * - Retain directory structure for ease of management
 * - Target output is ready-to-run HTMl/JS/CSS files, no build service after deployment
 *   since target environment may or may not have this ability.
 * - Continued use of SCRIPT tags and CDNs for loading third-party libraries
 *   for superior delivery speed compared to bundling.
 * - Compile ES2015 and LESS for developers, into vanilla JS and CSS files for browsers
 * - Interpolation of cache-busting hash into HTML script/css tags
 *
 * Presumed structure:
 *
 * - Typical Django multi-page app structure, in which view methods render() a HTML template
 *
 * - The .js6 files will require() the .less and .src.html files relevant to that page
 *
 * - The .js6 and .less files exist in a subdirectory structure such as static/
 *   and will be compiled to .js and .css files in the same folder as those source files
 *   these form client-delivered JS and CSS for each page
 *
 * - The .src.html files exist in a subdirectory structure such as templates/
 *   and will be compiled to .html files in the same folder as those source files
 *   these .html outputs are the templates to be used by Django
 *   though the .src.html sources would also work with Django and may be more expedient during development
 *
 * - For organization, it is recommended that these files follow naming conventions
 *   fitting their target page, e.g. about.js6   about.less   about.src.html
 *
 * - The .js6 files may require() additional .css and .js files from third-party libraries
 *   and will bundle them into the page's .css and .js outputs
 *   However, SCRIPT tags calling CDNs tend to give faster loading times than bundling and should usually
 *   be preferred for loading of third-party materials, unless there's a compelling reason to bundle.
 *
 * - The output .js .less .html files should be included in version control as browser deliverables,
 *   OR ELSE the deployment environment should include a mechanism to run the build. Up to you.
 *
 */

// the list of .js6 entry point files
// in addition to being ES2015 JavaScript code, these may require() the .src.html and .less files to also be compiled into their own outputs
// tip: require()ing other stuff, or even having JavaScript code in the file, is typical but optional
// you could have a .js6 file which effectively only serves to create a bundle of third-party code or a shared stylesheet

const JS6_FILES = [
    './home/index.js6',
    './about/index.js6',
    './scoreyours/index.js6',
];

/////////////////////////////////////////////////////////////////////////////////////////////////////////

const ExtractTextPlugin = require("extract-text-webpack-plugin");

var StringReplacePlugin = require("string-replace-webpack-plugin");

module.exports = {
    /*
     * multiple entry points, one per entry
     * the [name] for each is the basename, e.g. some/path/to/thing so we can add .js and .css suffixes
     * the values are the files with their .js6 suffixes retained
     */
    entry: JS6_FILES.reduce((o, key) => { o[key.replace(/\.js6$/, '')] = key; return o; }, {}),
    output: {
        path: __dirname,
        filename: '[name].js'
    },

    module: {
        loaders: [
            /*
             * Plain JS files
             * just kidding; Webpack already does those without any configuration  :)
             * but we do not want to lump them in with ES6 files: they would be third-party and then run through JSHint and we can't waste time linting third-party JS
             */

            /*
             * run .js6 files through Babel + ES2015 via loader; lint and transpile into X.js
             * that's our suffix for ECMAScript 2015 / ES6 files
             */
            {
                test: /\.(js|js6)$/,
                use: [
                    { loader: 'babel-loader', options: { presets: ['es2015'] } },
                    { loader: 'jshint-loader', options: { esversion: 6, emitErrors: true, failOnHint: true } }
                ],
                exclude: /node_modules/
            },

            /*
             * CSS files and also SASS-to-CSS all go into one bundled X.css
             */
            {
                test: /\.css$/,
                use: ExtractTextPlugin.extract({
                    use: [
                        { loader: 'css-loader', options: { minimize: true, sourceMap: true, url: false } }
                    ],
                    fallback: 'style-loader'
                })
            },
            {
                test: /\.scss$/,
                use: ExtractTextPlugin.extract({
                    use: [
                        { loader: 'css-loader', options: { minimize: true, sourceMap: true, url: false } },
                        { loader: 'sass-loader', options: { sourceMap:true } },
                    ],
                    fallback: 'style-loader'
                })
            },

            /*
             * HTML Files
             * replace [hash] entities in the .src.html to generate .html
             * typically used on .js and .css filenames to include a random hash for cache-busting
             * though could be used to cache-bust nearly anything such as images
             * tip: HTML file basenames (like any) should be fairly minimal: letters and numbers, - _ . characters
             */
            {
                test: /\.src\.html$/,
                use: [
                    {
                        loader: 'file-loader',
                        options: {
                            // replace .src.html with just .html
                            name: '[path][1].html',
                            regExp: '([\\w\\-\.]+)\\.src\\.html$',
                        },
                    },
                    {
                        loader: StringReplacePlugin.replace({
                        replacements: [
                            {
                                pattern: /\[hash\]/g,
                                replacement: function (match, p1, offset, string) {
                                    const randomhash = new Date().toString();
                                    return randomhash;
                                }
                            },
                        ]})
                    }
                ]
            },

            /*
             * Files to ignore
             * Notably from CSS, e.g. background-image SVG, PNGs, JPEGs, fonts, ...
             * we do not need them processed; our stylesheets etc. will point to them in their proper place
             * webpack scans the HTML files and will throw a fit if we don't account for every single file it finds
             */
            {
                test: /\.(svg|gif|jpg|jpeg|png)$/,
                loader: 'ignore-loader'
            },
            {
                test: /\.(woff|woff2|ttf|eot)$/,
                loader: 'ignore-loader'
            }
        ]
    },


    /*
     * enable source maps, applicable to both JS and CSS
     */
    devtool: "nosources-source-map",

    /*
     * plugins for the above
     */
    plugins: [
        // CSS output from the CSS + LESS handlers above
        new ExtractTextPlugin({
            disable: false,
            filename: '[name].css'
        }),
        // for doing string replacements on files
        new StringReplacePlugin(),
    ],

    /*
     * plugins for the above
     */
    devServer: {
      contentBase: '.',
      host: '0.0.0.0',
      port: 8000,
      disableHostCheck: true
    }
};
