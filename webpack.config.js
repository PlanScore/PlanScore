// the list of .js6 entry point files
// in addition to being ES2015 JavaScript code, these may require() the .src.html and .scss files to also be compiled into their own outputs
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
