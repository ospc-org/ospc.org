var less = require('gulp-less');
var path = require('path');
var gulp = require('gulp');
var sourcemaps = require('gulp-sourcemaps');

gulp.task('less', function () {
  return gulp.src('./static/less/*.less')
    .pipe(sourcemaps.init())
    .pipe(less({
      paths: [ path.join(__dirname, 'less', 'includes') ]
    }))
    .pipe(sourcemaps.write())
    .pipe(gulp.dest('./static/css'));
});

gulp.task('watch', function () {
  gulp.watch('static/less/**', ['less']);
});

gulp.task('default', ['less', 'watch']);