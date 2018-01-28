// the list of .js6 entry point files
// in addition to being ES2015 JavaScript code, these may require() the .src.html and .less files to also be compiled into their own outputs
// tip: require()ing other stuff, or even having JavaScript code in the file, is typical but optional
// you could have a .js6 file which effectively only serves to create a bundle of third-party code or a shared stylesheet

const JS6_FILES = [
    // home page and peripheral pages
    './index.js6',
    './error.js6',
    './about/index.js6',
    './scoreyours/index.js6',
    './historical-data/index.js6',
    './efficiencygap/index.js6',
    './meanmedian/index.js6',
    './partisanbias/index.js6',
    './sitewide.js6',
    './patternlibrary/index.js6',
    './patternlibrary_htmltemplate/index.js6',


    // per state pages, which really just use the same _statetemplate template
    './alabama/index.js6',
    './alaska/index.js6',
    './arizona/index.js6',
    './arkansas/index.js6',
    './california/index.js6',
    './colorado/index.js6',
    './connecticut/index.js6',
    './delaware/index.js6',
    './florida/index.js6',
    './georgia/index.js6',
    './hawaii/index.js6',
    './idaho/index.js6',
    './illinois/index.js6',
    './indiana/index.js6',
    './iowa/index.js6',
    './kansas/index.js6',
    './kentucky/index.js6',
    './louisiana/index.js6',
    './maine/index.js6',
    './maryland/index.js6',
    './massachusetts/index.js6',
    './michigan/index.js6',
    './minnesota/index.js6',
    './mississippi/index.js6',
    './missouri/index.js6',
    './montana/index.js6',
    './nebraska/index.js6',
    './nevada/index.js6',
    './new_hampshire/index.js6',
    './new_jersey/index.js6',
    './new_mexico/index.js6',
    './new_york/index.js6',
    './north_carolina/index.js6',
    './north_dakota/index.js6',
    './ohio/index.js6',
    './oklahoma/index.js6',
    './oregon/index.js6',
    './pennsylvania/index.js6',
    './rhode_island/index.js6',
    './south_carolina/index.js6',
    './south_dakota/index.js6',
    './tennessee/index.js6',
    './texas/index.js6',
    './utah/index.js6',
    './vermont/index.js6',
    './virginia/index.js6',
    './washington/index.js6',
    './west_virginia/index.js6',
    './wisconsin/index.js6',
    './wyoming/index.js6',
];

/////////////////////////////////////////////////////////////////////////////////////////////////////////

const ExtractTextPlugin = require("extract-text-webpack-plugin");
const StringReplacePlugin = require("string-replace-webpack-plugin");
const WriteFilePlugin = require("write-file-webpack-plugin");

const HTML_PARTIALS = {
    footer: require("./htmlpartials/footer"),
    navbar: require("./htmlpartials/navbar"),
    headtags: require("./htmlpartials/head"),
};

module.exports = {
    /*
     * multiple entry points, one per entry
     * the [name] for each is the basename, e.g. some/path/to/thing so we can add .js and .css suffixes
     * the values are the files with their .js6 suffixes retained
     */
    entry: JS6_FILES.reduce((o, key) => { o[key.replace(/\.js6$/, '')] = key; return o; }, {}),
    output: {
        path: __dirname,
        filename: 'WEBSITE_OUTPUT/[name].js'
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
                            name: 'WEBSITE_OUTPUT/[path][1].html',
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
                    },
                    {
                        loader: StringReplacePlugin.replace({
                        replacements: [
                            // a series of HTML partials to be interpolated
                            {
                                pattern: /\<!--\[include_footer\]-->/g,
                                replacement: function (match, p1, offset, string) {
                                    return HTML_PARTIALS.footer;
                                }
                            },
                            {
                                pattern: /\<!--\[include_navbar\]-->/g,
                                replacement: function (match, p1, offset, string) {
                                    return HTML_PARTIALS.navbar;
                                },
                            },
                            {
                                pattern: /\<!--\[include_head\]-->/g,
                                replacement: function (match, p1, offset, string) {
                                    return HTML_PARTIALS.headtags;
                                },
                            },
                        ]})
                    },
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
        // so webpack-dev-server will ALSO write files to disk in addition to in-memory
        new WriteFilePlugin(),
        // CSS output from the CSS + LESS handlers above
        new ExtractTextPlugin({
            disable: false,
            filename: 'WEBSITE_OUTPUT/[name].css'
        }),
        // for doing string replacements on files
        new StringReplacePlugin(),
    ],

    /*
     * plugins for the above
     */
    devServer: {
      contentBase: './WEBSITE_OUTPUT',
      host: '0.0.0.0',
      port: 8000,
      disableHostCheck: true
    }
};
