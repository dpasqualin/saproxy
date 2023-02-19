# SAProxy

This Simple Async Proxy was developed as an exercise for async programming in python.
It will forward any post requests to postman (used here as a dummy upstream
service) with a JWT appended to it and return the response unaltered back to the client.
The additional `/status` endpoint will return a json with the service uptime and the
number of requests served.

## Running it

You can start the proxy server in your favorite virtual environment manager or using
docker. For the first option run `make build` to install the dependencies and `make run`
to start the service on port `8080`. You can specify a different port by running
`HTTP_PORT=<port> make run`. Now if docker is the way for you run `docker compose build`
to create the image and `docker compose run` to start the service.

## Testing it

Make sure you have dependencies installed with `make build` and then run `make test`.

