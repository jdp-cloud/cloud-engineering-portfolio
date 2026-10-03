#!/bin/sh
# Runs once inside the `seed` container. Builds a throwaway git repository from this project's
# files so Jenkins has a real repository to check out, with two branches:
#   main             the clean app (every gate should pass)
#   vulnerable-demo  the same app with known-vulnerable dependency pins (a gate should block it)
set -eu

cd /seed
rm -rf repo
mkdir repo
cd repo

git init -q -b main
git config user.name "lab-seed"
git config user.email "seed@lab.invalid"

cp -R /project/app /project/terraform ./
cp /project/Jenkinsfile /project/sonar-project.properties /project/zap-rules.conf ./
# Local test runs leave caches behind; keep them out of the seeded repository.
rm -rf app/__pycache__ app/tests/__pycache__ app/.pytest_cache app/.coverage

git add -A
git commit -q -m "main: clean sample app"

git checkout -q -b vulnerable-demo
cp /project/demo/requirements.vulnerable.txt app/requirements.txt
git commit -q -am "vulnerable-demo: pin known-vulnerable dependencies"

git checkout -q main
chmod -R a+rX /seed/repo
echo "seeded repository:"
git branch --list
