var gulp = require('gulp');
var git = require('git-rev');
var fs = require('fs');

var del = require('del');
var typescript = require('gulp-typescript');
var Server = require('karma').Server;

// Squelch cachebuster output (it's really noisy)
var SystemJSCacheBuster = require("systemjs-cachebuster");
var cacheBuster = new SystemJSCacheBuster();
 
var distdir = './dist';
var reportdir = './reports';

var PATHS = {
    src: {
        css: [
            './css/**/*.css',
        ],
        html: [
            './src/**/*.html',
            './src/**/components/**/*.css'
        ],
        ts: './src/**/*.ts',
        js: [
          './dist/**/*.js'
        ]  
    },
    img: [
        './img/**/*.*'
    ]
};

var exitCode = 0;

process.on('exit', function() {
    process.exit(exitCode);
});

gulp.task('clean', function () {
    // delete contents of distdir but not distdir itself nor its .gitkeep file
    // (this way, if distdir itself is mounted to a docker container, the mount will survive)
    del.sync([distdir+"/*", "!"+distdir+"/.gitkeep", reportdir], {force: true});
});

// Copy component CSS and HTML templates
// TODO: Look up best practices for minifying component-relative files
gulp.task('html', function () {
    return gulp.src(PATHS.src.html).pipe(gulp.dest(distdir));
});

/*
TODO: lint / minify / compress css?
See https://www.npmjs.com/package/gulp-csslint
See https://www.npmjs.com/package/gulp-cssmin

gulp.task('css', function () {
    return gulp.src(PATHS.src.css).pipe(gulp.dest(distdir+'/css'));
});
*/

/*
TODO: compress images?
See https://www.npmjs.com/package/gulp-imagemin

gulp.task('img', function () {
    return gulp.src(PATHS.img).pipe(gulp.dest(distdir+'/img'));
});
*/

/*
TODO: lint / minify / compress generated js files?
See https://www.npmjs.com/package/gulp-uglify
See https://www.npmjs.com/package/gulp-jshint

*/


gulp.task('cachebuster:css', function () {
    return gulp.src(PATHS.src.css).pipe(cacheBuster.full())
});

gulp.task('cachebuster:html', [ 'html' ], function () {
    return gulp.src(PATHS.src.html).pipe(cacheBuster.full())
});

gulp.task('cachebuster:js', [ 'ts' ], function () {
    return gulp.src(PATHS.src.js).pipe(cacheBuster.full())
});


gulp.task('ts', function () {
    return gulp.src(PATHS.src.ts)
        .pipe(typescript({
            // TODO: look into this to remove relative paths from imports?
            //baseUrl: ".",
            noImplicitAny: true,
            module: 'commonjs',
            target: 'es5',
            noResolve: false,
            experimentalDecorators: true,
            emitDecoratorMetadata: true,
            noEmitOnError: true,
            moduleResolution: 'node',
            "sourceMap": true
        }))
        .on('error', function() {exitCode++;})
        .pipe(gulp.dest(distdir));
});

gulp.task('dist', [ /*'css', 'img',*/ 'ts', 'html', 'cachebuster:js', 'cachebuster:html' , 'cachebuster:css'  ], function () {
    // git-rev expose long or short SHA
    git.long(function (sha) {
        // TODO: Add more fields to this, as necessary / helpful
        var status = {
            sha: sha,
            runlevel: process.env.NEST_RUNLEVEL || 'development',
            hzHost: process.env.HUBZERO_APPLICATION_HOST || '',
            maxUploadSize: process.env.MAX_CONTENT_LENGTH || ''
        };
        fs.writeFileSync('dist/status.json', JSON.stringify(status));
        console.log('Status Written:', status);
    });
});

//run tests once and exit, suitable for testing in build environment like Jenkins
gulp.task('test', ['dist'], function () {
    // FIXME: Disabling this for now, as it fails intermittently on CI
    // see https://visualanalytics.atlassian.net/browse/TOOL-380
    /* new Server({
        configFile: __dirname + '/karma.conf.js',
        singleRun: true
    }, function(code) {exitCode = code;}).start(); */
});

//watch for file changes and re-run tests on each change, suitable for test driven development, aka, tdd
gulp.task('tdd', ['dist'], function (done) {
    new Server({
        configFile: __dirname + '/karma.conf.js',
    }, done).start();
});
