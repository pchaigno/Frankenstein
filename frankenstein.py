#!/usr/bin/env python3
import sys
import json
import os
import time
import re
import subprocess
import gauss
import random
import datetime

"""Dumps the logs from a git repository as a JSON document.

The call to this function must be made from the parent directory of the directory of the repository.
The logs are saved as a JSON document in the directory of the repository.
This function temporarily changes the current working directory.

Args:
	repository: The name of the folder where the repository is.

Returns:
	The logs as a Python array.
"""
def dump_logs(repository):
	os.chdir(repository)

	# Dumps the git logs in a JSON document.
	os.system("""git log --reverse --pretty=format:'{%n  "hash": "%H",%n  "author": "%an",%n  "author-email": "%ae",%n  "author-date": %at,%n  "committer": "%cn",%n  "committer-email": "%ce",%n  "committer-date": %ct,%n  "message": "%s"%n},' $@ | perl -pe 'BEGIN{print "["}; END{print "]\n"}' | perl -pe 's/},]/}]/' > logs.json""")

	# Rewrites the escaped JSON document in a new file.
	# Then, the original JSON document in overwritten with the new one:
	json_data = open('logs.json')
	json_escaped = open('logs-escaped.json', 'w')
	for line in json_data:
		matches = re.match(r'^  "message": "(.+)"$', line)
		if matches:
			# Escapes the backslashes first, the double quotes after
			# because we need to add a backslash to escape the double quotes:
			message = matches.group(1).replace('\\', '\\\\')
			message = message.replace('"', '\\"')
			line = '  "message": "%s"\n' % (message)
		json_escaped.write(line)
	json_data.close()
	json_escaped.close()
	os.system("mv logs-escaped.json logs.json")

	# Reads the git logs from the JSON document.
	json_data = open("logs.json")
	logs = json.load(json_data)
	json_data.close()
	
	os.chdir('..')

	return logs


"""Dumps the commits from a git repository as patch files.

The patch files are created into the repository directory.
This function temporarily changes the current working directory.

Args:
	repository: The name of the folder where the repository is.
	logs: The git logs as a Python array.
"""
def dump_commits(repository, logs):
	os.chdir(repository)

	# Uses the binary option to be able to dump and then apply the images and other binary files:
	os.system("git show --binary %s > 0.patch" % (logs[0]['hash']))
	for i in range(1, len(logs)):
		os.system("git diff --binary %s %s > %d.patch" % (logs[i-1]['hash'], logs[i]['hash'], i))

	os.chdir('..')


"""Rebuild a git repository from patches and with some modifications.

Uses the patch files and the git logs to rebuild a repository.
A commit is made between each patch applied.
The contributors can be replaced with the credentials specified.
All the committer and author dates will be shift by the offset value.

This function temporarily changes the current working directory.
It only reproduces the commit history and doesn't push it.
The user will need to add a remote repository (git remote add) before pushing.

Args:
	dump_folder: The directory containing the pach files and the JSON document.
	logs: The git logs as a Python array.
	repository: The directory name for the new repository.
	your_username: Your username. Will replace the contributors specified.
	your_email: Your email address. Will replace the email addresses of the contributors specified.
	contributors: The contributors to replace or all to replace all of them.
	offset: The offset (in seconds) of which the commit's dates must be shifted.
"""
def rebuild_repository(dump_folder, logs, repository, your_username, your_email, contributors = [], offset = 0):
	os.system("mkdir %s" % (repository))
	os.chdir(repository)

	os.system("git init")
	for i in range(0, len(logs)):
		log = logs[i]
		
		# Changes the committer and author (and their email addresses) and the dates if needed:
		committer = log['committer']
		committer_email = log['committer-email']
		if contributors == 'all' or committer_email in contributors:
			committer = your_username
			committer_email = your_email
		author = log['author']
		author_email = log['author-email']
		if contributors == 'all' or author_email in contributors:
			author = your_username
			author_email = your_email
		committer_date = log['committer-date'] + offset
		author_date = log['author-date'] + offset

		# Checks that the current dates hasn't been reached (we don't want to make commits in the future):
		current_time = (int)(time.time())
		if committer_date > current_time or author_date > current_time:
			print("Reached current date.")
			break

		# Apply the patch without displaying the command output.
		os.system("git apply --whitespace=nowarn ../%s/%d.patch 2> /dev/null " % (dump_folder, i))
		os.system("git add --all .")

		# The values for the committer can only be changed through the environnement variables:
		os.environ["GIT_COMMITTER_NAME"] = committer
		os.environ["GIT_COMMITTER_EMAIL"] = committer_email
		os.environ["GIT_COMMITTER_DATE"] = str(committer_date)

		# Need to escape the double quotes for the commit message.
		message = log['message'].replace('"', '\\"')
		
		# Quiet mode for the commits, only the errors are shown.
		return_code = os.system("""git commit -q -m "%s" --author="%s <%s>" --date=%d""" % (message, author, author_email, author_date))
		
	os.chdir('..')


"""Gets the email addresses of the contributors of a repository.

The following git command is used: git log --format='%ae' | sort -u.
This function temporarily changes the current working directory.

Args:
	repository: The name of the folder where the repository is.

Returns:
	The list of contributors' email addresses.
"""
def get_contributors(repository):
	os.chdir(repository)
	process1 = subprocess.Popen(('git', 'log', '--format=%ae'), stdout=subprocess.PIPE)
	process2 = subprocess.Popen(('sort', '-u'), stdin=process1.stdout, stdout=subprocess.PIPE)
	contributors = process2.stdout.read().decode('utf-8').split("\n")
	os.chdir('..')
	return contributors


"""Find a streak of 50 commits in a month.

It actually searches for a streak in 29 days.
The search starts with the last commit so that the the lastest streak will be returned.
The author dates are used as reference dates.
It is possible to specify an author (via his email address) to whom all commits must belong.

Args:
	logs: The git logs as a Python array.
	author: The author for the streak or None if no author is needed.

Returns:
	The number of the last commit from the streak.
	-1 if no streak is found.
"""
def find_50commits_month(logs, author = None):
	for i in range(len(logs)-1, 50, -1):
		nb_commits = 0
		for j in range(i-1, 0, -1):
			if author != None and logs[j]['author-email'] == author:
				period = logs[i]['author-date'] - logs[j]['author-date']
				if period > 29 * 24 * 3600:
					break
				if nb_commits >= 50:
					return i
				nb_commits += 1
	return -1


"""Find a contributor who made 50 commits in a month.

Iterates on all the contributors until it finds one with 50 commits in a month.

Args:
	repository: The name of the folder where the repository is.
	logs: The git logs as a Python array.

Returns:
	A tuple with the contributor email address and the number of the last commit from the streak he made.
	A tuple with None and -1 if no contributor streak is found.
"""
def find_contributor_50commits_month(repository, logs):
	contributors = get_contributors(repository)
	for contributor in contributors:
		num_commit = find_50commits_month(logs, contributor)
		if num_commit != -1:
			return (contributor, num_commit)
	return (None, -1)


"""Computes the time offset to put the last commit today.

Args:
	logs: The git logs as a Python array.
	num_commit: The number of the commit we want as last.

Returns:
	The offset to apply in seconds.
"""
def compute_offset(logs, num_commit):
	return int(time.time()) - logs[num_commit]['author-date']


"""Computes the time period of the commits.

The term time designates here the time in the day.
Thus, this function finds between which hours the commits were made until now.

Args:
	logs: The git logs as a Python array.

Returns:
	A tuple with the minimum and maximum of the time period.
"""
def compute_commit_time_period(logs):
	min_time = 3600 * 24
	max_time = 0
	for i in range(start_commit, end_commit):
		log = logs[i]
		commit_date = datetime.datetime.fromtimestamp(log['author-date'])
		commit_time = commit_date.hour * 3600 + commit_date.minute * 60 + commit_date.second
		if commit_time > max_time:
			max_time = commit_time
		if commit_time < min_time:
			min_time = commit_time
	return (min_time, max_time)


"""Redistributes the last commits of a repository to put at least 50 of them in a month.

Selects 50 or more commits and squashes them into a month.

Args:
	logs: The git logs as a Python array.
	num_commit: The number of the last commit from the 50 we want to squash.
"""
def redistribute_commits(logs, num_commit):
	numbers_of_commits = gauss.generate_in_range(5.0/3, 29, 50, 60)
	if len(numbers_of_commits) != 29:
		raise("Incorrect number of commit numbers generated by the Gauss distribution.")
	total_commits = sum(numbers_of_commits)
	start_commit = num_commit - total_commits + 1
	end_commit = num_commit
	(min_time, max_time) = compute_commit_time_period(logs[start_commit: end_commit])
	start_date = int(time.mktime(datetime.datetime.fromtimestamp(logs[start_commit]['author-date']).date().timetuple()))
	num_commit = start_commit
	for num_day in range(0, 29):
		day = start_date + num_day * 24 * 3600
		for i in range(0, numbers_of_commits[num_day]):
			commit_time = random.randint(min_time, max_time)
			timestamp = day + commit_time
			logs[num_commit]['author-date'] = timestamp
			logs[num_commit]['committer-date'] = timestamp
			num_commit += 1


"""Try different methods to add 50 commits in a month to the user from an existing repository.

Usage: frankenstein.py <repository> <new-name> <your-email> <your-name>

Args:
	repository: The existing repository.
	new_name: The name of the repository to be created.
	your_email: The email of the user (must be linked to his GitHub account).
	your_name: The name of the user (will appear on GitHub).
"""
if __name__ == "__main__":
	if len(sys.argv) < 5:
		print("Usage: frankenstein.py <repository> <new-name> <your-email> <your-name>")
		sys.exit(2)

	repository = sys.argv[1]
	new_repository = sys.argv[2]
	your_email = sys.argv[3]
	your_name = sys.argv[4]

	# Dumps the git logs from the repository to a JSON document.
	logs = dump_logs(repository)

	# We only use existing commits so we need at least 50 of them:
	if len(logs) < 50:
		print("Not enough commits in this repository.")
		sys.exit(1)

	# Dumps the commits from the repository as .patch files:
	print("Dumping commits in patches...")
	dump_commits(repository, logs)

	# Searches for 50 commits in a month under the name of the user.
	# Only copy the repository with a time shift to put the streak in the last month if a streak is found.
	print("Checking if you made 50 commits in a month...")
	num_commit = find_50commits_month(logs, your_email)
	if num_commit != -1:
		print("You made 50 commits in a month with %d as last commit" % (num_commit))
		offset = compute_offset(logs, num_commit)
		rebuild_repository(repository, logs, new_repository, your_name, your_email, [], offset)
		sys.exit(0)

	# Searches for a contributor with 50 commits in a month.
	# If found, the contributor will be replaced with the user of the script.
	# During the copy the date will be shifted as before.
	print("Searching for a contributor with 50 commits in a month...")
	(contributor, num_commit) = find_contributor_50commits_month(repository, logs)
	if contributor != None:
		print("%s made 50 commits in a month with %d as last commit" % (contributor, num_commit))
		offset = compute_offset(logs, num_commit)
		rebuild_repository(repository, logs, new_repository, your_name, your_email, [contributor], offset)
		sys.exit(0)

	# Searches for a month with 50 commits.
	# If found, all contributors to the project will be replaced with the user of the script.
	# Then, the date will be shifted during the copy as before.
	print("Searching for a month with 50 commits...")
	num_commit = find_50commits_month(logs)
	if num_commit != -1:
		print("50 commits in a month were found ending with commit %d" % (num_commit))
		offset = compute_offset(logs, num_commit)
		rebuild_repository(repository, logs, new_repository, your_name, your_email, 'all', offset)
		sys.exit(0)

	# Squashes 50 or more commit dates to put them in a month.
	# Then, the date are shifted as before to put the 50 squashed commits in the last month.
	last_commit = len(logs) - 1
	redistribute_commits(logs, last_commit)
	offset = compute_offset(logs, last_commit)
	rebuild_repository(repository, logs, new_repository, your_name, your_email, 'all', offset)
	sys.exit(0)
