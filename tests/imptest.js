casper.test.begin('Test that all routes return 200', function(test) {
    casper.start('http://localhost:8888/', function() {
        test.assertHttpStatus(200, 'The root page should load');
    });

    casper.thenOpen('http://localhost:8888/images/', function() {
        test.assertHttpStatus(200, 'The images page should load');
    });

    casper.thenOpen('http://localhost:8888/tags/', function() {
        test.assertHttpStatus(200, 'The tags page should load');
    });

    casper.thenOpen('http://localhost:8888/categories/', function() {
        test.assertHttpStatus(200, 'The categories page shoul load');
    });

    casper.run(function() {
        test.done();
    });
});
