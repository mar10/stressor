# Development

Run in virtual environmment:

```bash
$ pipenv shell
$ pipenv install
$ stressor -h
```

Run in a virtual debugging environmment:

```bash
$ pipenv shell
$ pipenv install --dev
$ tox
$ pipenv install --dev -e .
$ stressor -h
```
