#!/usr/bin/env python3
import random

def gauss():
	numbers = []
	for i in range(0, 29):
		number = (int)(random.gauss(5/3, 1))
		if number >= 0 or number < 4:
			numbers.append(number)
	return numbers


def gauss_range(min_sum, max_sum):
	numbers = gauss()
	total = sum(numbers)
	while total < 50 or total > 60:
		numbers = gauss()
		total = sum(numbers)
	return numbers


if __name__ == "__main__":
	numbers = gauss_range(50, 60)
	total = sum(numbers)
	mean = total / len(numbers)
	print("sum=%d" % total)
	print("mean=%f" % mean)
