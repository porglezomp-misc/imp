casper.test.begin('Test the critical paths of the application', function(test) {
    casper.start('http://localhost:8888/', function() {
        test.assertHttpStatus(200, 'The root page should load');
        test.assertExists('a[href="/images/new"]',
                          'The page should have a link to add a new image');
        this.click('a[href="/images/new"]');
    });

    casper.waitForUrl('http://localhost:8888/images/new', function() {
        test.assertHttpStatus(200, 'The new images page should load');
        test.assertExists('form[action="/images/new"]',
                          'The page should have a form to describe the image');
        this.fill('form[action="/images/new"]', {
            name: 'My Steven Universe Poster!',
            url: 'http://i.imgur.com/Cy0QxaE.jpg',
            description: 'An extremely cool poster',
        }, true);
    });

    casper.waitForUrl('http://localhost:8888/images/Cy0QxaE', function() {
        test.assertHttpStatus(200, 'The newly created image page should load');
        test.assertTitle('My Steven Universe Poster!',
                         'The page should have the title we entered');
        // TODO: The header should also have the title we entered
        test.assertExists('img[src="http://i.imgur.com/Cy0QxaE.jpg"]',
                          'The image we chose should be on the page');
    });

    casper.thenOpen('http://localhost:8888/images/', function() {
        test.assertHttpStatus(200, 'The images page should load');
    });

    casper.thenOpen('http://localhost:8888/tags/', function() {
        test.assertHttpStatus(200, 'The tags page should load');
    });

    casper.thenOpen('http://localhost:8888/categories/', function() {
        test.assertHttpStatus(200, 'The categories page should load');
    });

    casper.run(function() {
        test.done();
    });
});
