#!/usr/bin/env python3
import sys
import os
import re
import json
import subprocess
import time

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
		result = os.system("git diff --binary %s %s > %d.patch" % (logs[i-1]['hash'], logs[i]['hash'], i))

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
		# allow-empty option for commits containing nothing (merge commits for example).
		return_code = os.system("""git commit --allow-empty -q -m "%s" --author="%s <%s>" --date=%d""" % (message, author, author_email, author_date))
		
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


if __name__ == "__main__":
	if len(sys.argv) < 3:
		print("Usage: git.py <repository> <new-name>")
		sys.exit(2)

	repository = sys.argv[1]
	new_repository = sys.argv[2]

	contributors = get_contributors(repository)
	print(contributors)

	logs = dump_logs(repository)
	dump_commits(repository, logs)
	rebuild_repository(repository, logs, new_repository, '', '', [], 0)


"""Clones a repository.

Args:
	url: The URL to the git repository (need to be HTTP or HTTPS).

Returns:
	The folder where the repository was downloaded.
"""
def clone_repository(url):
	os.system("git clone %s" % url)
	print()

	matches = re.match(r'https?:\/\/.+\/([^\/]+)(\.git)?$', url)
	if not matches:
		raise Exception("You need to provide a HTTP(S) link.")
	repository = matches.group(1)
	return repository
