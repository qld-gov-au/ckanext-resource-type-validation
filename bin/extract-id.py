# encoding: utf-8
import json
import sys

print(json.loads(sys.stdin.read())['result']['id'])
