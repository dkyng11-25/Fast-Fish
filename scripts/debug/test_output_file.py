#!/usr/bin/env python3

# Simple test to write output to a file instead of stdout
with open('test_output.txt', 'w') as f:
    f.write('Test output from Python script\n')
    f.write('This should create a file with some content\n')

print('Test completed - check test_output.txt')
