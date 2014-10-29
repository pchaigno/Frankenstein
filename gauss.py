#!/usr/bin/env python3
import random

def gauss():
	numbers = []
	for i in range(0, 29):
		number = (int)(random.gauss(5/3, 1))
		if number >= 0 or number < 4:
			numbers.append(number)
	return numbers


if __name__ == "__main__":
	numbers = gauss()
	total = sum(numbers)
	while total < 50 or total > 60:
		numbers = gauss()

	mean = total / len(numbers)
	print("sum=%d" % total)
	print("mean=%f" % mean)
