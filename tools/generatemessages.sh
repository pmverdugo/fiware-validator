#!/usr/bin/env bash
# Generate messages and translation files
pybabel extract -F babel.cfg -k lazy_gettext -o validator/locale/validator.pot .
pybabel init -i validator/locale/validator.pot -d translations -l es