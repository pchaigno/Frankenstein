#!/usr/bin/env python3
import random
import datetime
import sys
import time
import os

"""Error raised when character is not defined.

Attributes:
	character: The character which is not defined.
"""
class UndefinedCharacterError(Exception):
	def __init__(self, character):
		self.character = character

	def __str__(self):
		return "The encoding for the character %s is not defined." % self.character


"""Gets the encoding as indexes for a character.

Encode the character as a list of pixels.
The pixels are represented by indexes in the contribution graph:
0 is at the top left corner, 6 at the bottom left corner, 7 at the top of the second column:
0 7  14 21 28
1 8  15 22 29
2 9  16 23 30
3 10 17 24 31
4 11 18 25 32
5 12 19 26 33
6 13 20 27 34
Only the five first lines are used such that if the drawing takes two days to appear, it will still be valid.
Otherwise, a pixel at the bottom of the graph would go to the top of the next column.

Args:
	character: The character to encode.

Returns:
	The encoding for the character as a tuple containing:
	- a list of indexes for the positions of each pixel of the character;
	- the width of the character including the free column after it.
"""
def get_character_encoding(character):
	characters = {
		'a': ([1, 2, 3, 4, 7, 9, 14, 16, 22, 23, 24, 25], 5),
		'b': ([0, 1, 2, 3, 4, 7, 9, 11, 14, 16, 18, 22, 24], 6),
		'c': ([1, 2, 3, 7, 11, 14, 18], 4),
		'd': ([0, 1, 2, 3, 4, 7, 11, 14, 18, 22, 23, 24], 5),
		'e': ([0, 1, 2, 3, 4, 7, 9, 11, 14, 18], 4),
		'f': ([0, 1, 2, 3, 4, 7, 9, 14], 4),
		'g': ([1, 2, 3, 7, 11, 14, 16, 18, 21, 23, 24, 25], 5),
		'h': ([0, 1, 2, 3, 4, 9, 16, 21, 22, 23, 24, 25], 5),
		'i': ([0, 4, 7, 8, 9, 10, 11, 14, 18], 4),
		'j': ([3, 7, 11, 14, 15, 16, 17, 18, 21], 5),
		'k': ([0, 1, 2, 3, 4, 9, 15, 17, 21, 25], 5),
		'l': ([0, 1, 2, 3, 4, 11, 18], 4),
		'm': ([0, 1, 2, 3, 4, 8, 16, 22, 28, 29, 30, 31, 32], 6),
		'n': ([0, 1, 2, 3, 4, 8, 16, 24, 28, 29, 30, 31, 32], 6),
		'o': ([1, 2, 3, 7, 11, 14, 18, 21, 25, 29, 30, 31], 6),
		'p': ([0, 1, 2, 3, 4, 7, 9, 14, 16, 22], 5),
		'q': ([1, 2, 3, 7, 11, 14, 18, 21, 24, 25, 29, 30, 31, 32], 6),
		'r': ([0, 1, 2, 3, 4, 7, 9, 14, 16, 17, 22, 25], 5),
		's': ([1, 7, 9, 11, 14, 16, 18, 21, 23, 25, 31], 6),
		't': ([0, 7, 8, 9, 10, 11, 14], 4),
		'u': ([0, 1, 2, 3, 11, 18, 25, 28, 29, 30, 31], 6),
		'v': ([0, 1, 9, 10, 18, 23, 24, 28, 29], 6),
		'w': ([0, 1, 2, 3, 4, 10, 16, 24, 28, 29, 30, 31, 32], 6),
		'x': ([0, 4, 8, 10, 16, 22, 24, 28, 32], 6),
		'y': ([0, 4, 8, 10, 16, 22, 28], 6),
		'z': ([0, 4, 7, 10, 11, 14, 16, 22, 18, 21, 25, 28, 32], 6)
	}
	if not character in characters:
		raise UndefinedCharacterError(character)
	return characters[character]


"""Computes the encoding for a string of characters.

Args:
	string: The string of characters. Must onyl contain English letters.

Returns:
	The encoding for the string of characters.
	A list of indexes for the positions of each pixel.
"""
def compute_string_encoding(string):
	string_encoding = []
	offset = 0
	for character in string:
		character_encoding = get_character_encoding(character)
		for index in character_encoding[0]:
			string_encoding.append(offset + index)
		offset += character_encoding[1] * 7
	return string_encoding


"""Computes the dates from an encoded string.

Each pixel from the string correspond to a date in the GitHub contribution graph.

Args:
	start_date: The date where the drawing should start.
	string_encoding: The encoded string as a list of indexes for the positions of each pixel.

Returns:
	A list of dates where pixels should be drawn.
"""
def compute_dates(start_date, string_encoding):
	dates = []
	time_in_day = 5 * 3600 + random.randint(0, 60)
	for index in string_encoding:
		timestamp = start_date + index * 24 * 3600 + time_in_day
		time_in_day += 60
		dates.append(timestamp)
	return dates


"""Creates a git repository.

Creates the folder and git init it.
This function temporarily changes the current working directory to perform the git init.

Args:
	name: The name for the new repository (name of the directory).
"""
def create_repository(name):
	os.system("mkdir %s" % (name))
	os.chdir(name)
	os.system("git init -q")
	os.chdir("..")


"""Draws pixels in the activity grapĥ.

Just makes 20 empty commits on the days specified.
This function temporarily changes the current working directory.

Args:
	repository: The name of the directory where the repository is.
	username: The name to commit under (author AND committer).
	email: The email to commit under (author AND committer).
	days: The dates of the days where the pixels should be, as timestamps.
"""
def draw_pixels(repository, username, email, days):
	os.environ["GIT_COMMITTER_NAME"] = username
	os.environ["GIT_COMMITTER_EMAIL"] = email

	os.chdir(repository)
	for day in days:
		for i in range(0, 40):
			os.environ["GIT_COMMITTER_DATE"] = str(day)
			os.system("""git commit --allow-empty -q -m "Update README" --author="%s <%s>" --date=%d""" % (username, email, day))
	os.chdir('..')


"""Reads the dates from the list file.

The dates must be in a file under the format:
day1:month1:year1
day2:month2:year2

Args:
	dates_file
"""
def read_dates(dates_file):
	dates = []
	time_in_day = 5 * 3600 + random.randint(0, 60)
	fh = open(dates_file, 'r')
	for line in fh:
		date_components = line.split(":")
		if len(date_components) == 3:
			year = int(date_components[2])
			month = int(date_components[1])
			day = int(date_components[0])
			date = datetime.date(year=year, month=month, day=day)

			time_in_day += 60
			timestamp = int(time.mktime(day.timetuple())) + time_in_day
			dates.append(timestamp)
	return dates


"""Draws pixels in the activity graph of some GitHub user.

Usage: git_pixel.py <repository> <source> <username> <email>

Args:
	repository: The name for the repository to create.
	date-file: Source for the pixel's indexes. Can be a path to a file with dates or a simple string.
	username: The GitHub user's name
	email: The email for the GitHub user.
"""
if __name__ == "__main__":
	if len(sys.argv) < 3:
		print("Usage: git_pixel.py <repository> <source> <username> <email>")
		sys.exit(2)

	repository = sys.argv[1]
	source = sys.argv[2]
	username = sys.argv[3]
	email = sys.argv[4]

	create_repository(repository)
	dates = []
	if os.path.isfile(source):
		dates = read_dates(source)
	else:
		try:
			string_encoding = compute_string_encoding(source)
		except UndefinedCharacterError as error:
			print(error)
			sys.exit(3)
		start_date = int(time.mktime(datetime.date(year=2014, month=2, day=9).timetuple()))
		dates = compute_dates(start_date, string_encoding)
	draw_pixels(repository, username, email, dates)
