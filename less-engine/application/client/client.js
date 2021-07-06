const http = require('http');

const options = {
    hostname: 'ae1c8aa3acf604b7fabd690454f9da30-1901306864.us-west-2.elb.amazonaws.com',
    port: 5377,
    path: '/',
    method: 'POST'
};

const req = http.request(options, (res) => {

    console.log(`statusCode: ${res.statusCode}`);

    res.on('data', (d) => {

        process.stdout.write(d);
    });
});

req.on('error', (err) => {

    console.error(err);
});

req.end();
