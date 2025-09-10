#!/usr/bin/env python3
"""
Example Python script for testing gist creation
"""

def fibonacci(n):
    """Calculate fibonacci number"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

if __name__ == "__main__":
    for i in range(10):
        print(f"fib({i}) = {fibonacci(i)}")