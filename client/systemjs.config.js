(function(global) {
  System.config({
    warnings: true,
    paths: {
      'npm:': 'node_modules/',
      
      'systemjs': 'node_modules/systemjs/dist/system.js',
      'es-module-loader': 'node_modules/es6-module-loader/dist/es-module-loader.js',
      'traceur': 'node_modules/traceur/bin/traceur-runtime.js',
    },
    map: {
      'dist': 'dist',
      'src': 'src',
      
      'angular2-jwt': 'npm:angular2-jwt/angular2-jwt.js',
      '@angular/core': 'npm:@angular/core/bundles/core.umd.js',
      '@angular/common': 'npm:@angular/common/bundles/common.umd.js',
      '@angular/compiler': 'npm:@angular/compiler/bundles/compiler.umd.js',
      '@angular/forms': 'npm:@angular/forms/bundles/forms.umd.js',
      '@angular/http': 'npm:@angular/http/bundles/http.umd.js',
      '@angular/router': 'npm:@angular/router/bundles/router.umd.js',
      '@angular/platform-browser': 'npm:@angular/platform-browser/bundles/platform-browser.umd.js',
      '@angular/platform-browser-dynamic': 'npm:@angular/platform-browser-dynamic/bundles/platform-browser-dynamic.umd.js',

      'file-saver': 'npm:file-saver/FileSaver.min.js',
      'rxjs': 'npm:rxjs',
      
      'moment': 'npm:moment/moment.js',
      'ngx-bootstrap': 'npm:ngx-bootstrap/bundles/ngx-bootstrap.umd.js',
      'ng2-slimscroll': 'npm:ng2-slimscroll/bundles/ng2-slimscroll.umd.js',
      'ng2-file-upload': 'npm:ng2-file-upload/bundles/ng2-file-upload.umd.js',
      'angular2-draggable': 'npm:angular2-draggable',
      
      crypto: '@empty'
    },
    packages: {
      
      // TypeScript source
      'src': {
        defaultExtension: 'ts'
      },
      
      // Transpiled JavaScript
      'dist': {
        defaultExtension: 'js'
      },
      
      'rxjs': {
        defaultExtension: 'js'
      },
      
      'file-saver': {
        format: "cjs"
      },
      
      'moment': { 
        defaultExtension: 'js'
      },
      
      'ngx-bootstrap': { 
        defaultExtension: 'js'
      },
      
      'ng2-slimscroll': {
        defaultExtension: 'js'
      },
      
      'ng2-file-upload': {
        defaultExtension: 'js'
      },
      
      'angular2-draggable': {
        defaultExtension: 'js',
        main: 'bundles/angular2-draggable.umd.min.js'
      }
    }
  })
})(this);