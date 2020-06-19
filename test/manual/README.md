# Tessumod manual test environment
This tool provides a manual test environment where Tessumod can be tested against a test TeamSpeak server. The environment includes a music bot (https://github.com/Splamy/TS3AudioBot) which can be commanded to play audio streams.

## Setup

First, you will need to have following:
* bash
* pipenv
* docker
* docker-compose
* TeamSpeak client
* World of Tanks, with Tessumod installed on it

Then install tool's python dependencies with command:
```bash
$ pipenv install
```

With dependencies installed you can startup the enviroment with:
```bash
$ ./test-environment env-up
```
You can then use your TeamSpeak client to connect `localhost` to join the test server.

## Testing

TBD

## Shutdown

You can bring down the environment with command:
```bash
$ ./test-environment env-stop
```

Or if you want to both bring it down and remove all resources use command:
```bash
$ ./test-environment env-down
```
