#!/usr/bin/env python3
import random

"""Generates a set of numbers following a Gaussian distribution.

Args:
	mean: The mean of the set.
	length: The size of the set.

Returns:
	The set of numbers as a Python array.
"""
def generate(mean, length):
	numbers = []
	for i in range(0, length):
		number = (int)(random.gauss(mean, 1))
		if number >= 0 or number < 4:
			numbers.append(number)
	return numbers


"""Generates a set of numbers following a Gaussian distribution and whose sum if in the specified range.

The sum of all the numbers from the set generated must be in the range specified.
Calls the generate function until the range condition is met.

Args:
	mean: The mean of the set.
	length: The size of the set.
	min_sum: Lower bound of the range, included.
	max_sum: Upper bound of the range, included.

Returns:
	The set of numbers as a Python array.
"""
def generate_in_range(mean, length, min_sum, max_sum):
	numbers = generate(mean, length)
	total = sum(numbers)
	while total < 50 or total > 60:
		numbers = generate(mean, length)
		total = sum(numbers)
	return numbers


if __name__ == "__main__":
	numbers = generate_in_range(5.0/3, 29, 50, 60)
	total = sum(numbers)
	mean = total / len(numbers)
	print("len=%d" % len(numbers))
	print("sum=%d" % total)
	print("mean=%f" % mean)
