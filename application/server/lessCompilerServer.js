const PORT = 5377; // (spells "LESS" on a phone-pad)
const WORKER_COUNT = 4;

// built-in (don't install with npm)
var cluster = require('cluster');

var winston = require('winston');
var format = require('logform');
var express = require('express');
var bodyParser = require('body-parser');
var less = require('less');
var fs = require('fs')

var log = createLogger();

if (cluster.isMaster) {
    log.info("Starting up (environment: %s)", process.env.NODE_ENV);

    for (var i = 0; i < WORKER_COUNT; i++) {
        cluster.fork();
    }

    process.on('SIGTERM', shutdown);
    process.on('SIGINT', shutdown);
} else {
    var server = express();

    server.use(bodyParser.text({limit: '5mb'}));

    server.post('/', function(req, res) {
        compile(req, res, {javascriptEnabled: true});
    });

    server.post('/min', function(req, res) {
        compile(req, res, {javascriptEnabled: true, compress: true});
    });

    server.listen(PORT, function() {
        log.info("Worker %s listening on port %s", cluster.worker.id, PORT);
    });
}

function compile(req, res, options) {
    var input = fs.readFileSync('lessengine-1267109827953998259.less', 'utf8');

    log.debug("Input (worker: %s, traceId: %s):\n" + input,
            cluster.worker.id, req.header("X-ANS-TraceID"));

    var start = new Date().getTime();

    less.render(input, options)
            .then(function(output) {
                var end = new Date().getTime();
                var css = output.css;

                log.debug("Output (worker: %s, traceId: %s):\n" + css,
                        cluster.worker.id, req.header("X-ANS-TraceID"));

                log.info("Compiled %d chars of LESS into %d chars of CSS in"
                        + " %d milliseconds (worker: %s, traceId: %s)",
                        input.length, css.length, (end - start),
                        cluster.worker.id, req.header("X-ANS-TraceID"));

                res.status(200).set('Content-Type', 'text/css').send(css);
            }, function(error) {
                log.error(error + " (worker: %s, traceId: %s)",
                        cluster.worker.id, req.header("X-ANS-TraceID"));

                res.status(error.type == "Parse" ? 400 : 500).send(error);
            });
}

function createLogger() {
    var logFormat = winston.format.printf(({ timestamp, level, message }) => {
        return `${timestamp} - ${level}: ${message}`;
    });

    return winston.createLogger({
        format: winston.format.combine(
                winston.format.splat(),
                winston.format.timestamp({format: 'YYYY-MM-DD HH:mm:ss,SSS'}),
                logFormat
        ),
        transports: [new (winston.transports.File)({
            silent: true, // change to false to enable debug log
            name: 'debug',
            filename: 'log/debug.log',
            level: 'debug',
            json: false,
            maxsize: 10485760,
            maxFiles: 5,
            tailable: true
        }), new (winston.transports.File)({
            name: 'info',
            filename: 'log/info.log',
            level: 'info',
            json: false,
            maxsize: 1048576,
            maxFiles: 5,
            tailable: true,
            handleExceptions: true,
            humanReadableUnhandledException: true
            //exitOnError: false // documented as being dangerous
        })]
    });
}

function shutdown() {
    log.info("Shutting down");
    log.close();

    process.exit();
}
