#!/usr/bin/env python3
import sys
import json
import os
import time
import re
import subprocess

def dump_logs(repository):
	os.chdir(repository)

	os.system("""git log --reverse --pretty=format:'{%n  "hash": "%H",%n  "author": "%an",%n  "author-email": "%ae",%n  "author-date": %at,%n  "committer": "%cn",%n  "committer-email": "%ce",%n  "committer-date": %ct,%n  "message": "%s"%n},' $@ | perl -pe 'BEGIN{print "["}; END{print "]\n"}' | perl -pe 's/},]/}]/' > logs.json""")

	json_data = open('logs.json')
	json_escaped = open('logs-escaped.json', 'w')
	for line in json_data:
		matches = re.match(r'^  "message": "(.+)"$', line)
		if matches:
			message = matches.group(1).replace('"', '\\"')
			line = '  "message": "%s"\n' % (message)
		json_escaped.write(line)
	json_data.close()
	json_escaped.close()
	os.system("mv logs-escaped.json logs.json")

	json_data = open("logs.json")
	logs = json.load(json_data)
	json_data.close()
	
	os.chdir('..')

	return logs


def dump_commits(repository):
	os.chdir(repository)
	json_data = open("logs.json")
	logs = json.load(json_data)
	json_data.close()

	os.system("git show --binary %s > 0.patch" % (logs[0]['hash']))
	for i in range(1, len(logs)):
		os.system("git diff --binary %s %s > %d.patch" % (logs[i-1]['hash'], logs[i]['hash'], i))

	os.chdir('..')


"""
contributors Contributors to replace.
"""
def rebuild_repository(dump_folder, repository, your_username, your_email, contributors = [], offset = 0):
	

	os.system("mkdir %s" % (repository))
	os.chdir(repository)

	json_data = open("../%s/logs.json" % (dump_folder))
	logs = json.load(json_data)
	json_data.close()

	os.system("git init")
	for i in range(0, len(logs)):
		log = logs[i]
		
		committer = log['committer']
		committer_email = log['committer-email']
		if contributors == 'all' or committer in contributors:
			committer = your_username
			committer_email = your_email
		author = log['author']
		author_email = log['author-email']
		if contributors == 'all' or author in contributors:
			author = your_username
			author_email = your_email
		committer_date = log['committer-date'] + offset
		author_date = log['author-date'] + offset

		current_time = (int)(time.time())
		if committer_date > current_time or author_date > current_time:
			print("Reached current date.")
			break

		os.system("git apply --whitespace=nowarn ../%s/%d.patch" % (dump_folder, i))
		os.system("git add --all .")
		os.environ["GIT_COMMITTER_NAME"] = committer
		os.environ["GIT_COMMITTER_EMAIL"] = committer_email
		os.environ["GIT_COMMITTER_DATE"] = str(committer_date)
		os.system("""git commit -m "%s" --author="%s <%s>" --date=%d""" % (log['message'], author, author_email, author_date))

	os.chdir('..')


def get_contributors(repository):
	os.chdir(repository)
	process1 = subprocess.Popen(('git', 'log', '--format=%ae'), stdout=subprocess.PIPE)
	process2 = subprocess.Popen(('sort', '-u'), stdin=process1.stdout, stdout=subprocess.PIPE)
	contributors = process2.stdout.read().decode('utf-8').split("\n")
	os.chdir('..')
	return contributors


def find_50commits_month(logs, author = None):
	for i in range(len(logs)-1, 50, -1):
		nb_commits = 0
		for j in range(i-1, 0, -1):
			if author != None and logs[j]['author-email'] == author:
				period = logs[i]['author-date'] - logs[j]['author-date']
				if period > 30 * 24 * 3600:
					break
				if nb_commits >= 50:
					print("Match found for %s! (n%d => -%d)" % (author, i, len(logs) - i))
					return i
				nb_commits += 1
	return -1


def find_contributor_50commits_month(repository, logs):
	contributors = get_contributors(repository)
	for contributor in contributors:
		num_commit = find_50commits_month(logs, contributor)
		return (contributor, num_commit)
	return (None, -1)


def compute_offset(logs, num_commit):
	return (int)(time.time()) - logs[num_commit]['author-date']


def compute_commit_time_period(logs, start_commit, end_commit):
	min_time = 3600 * 24
	max_time = 0
	for i in range(start_commit, end_commit):
		log = logs[i]
		date = datetime.fromtimestamp(log['author-date'])
		time = date.hour * 3600 + date.minutes * 60 + date.second
		if time > max_time:
			max_time = time
		if time < min_time:
			min_time = time 
	return (min_time, max_time)


if __name__ == "__main__":
	if len(sys.argv) < 5:
		print("Usage: frankenstein.py <repository> <new-name> <your-email> <your-name>")
		sys.exit(2)

	repository = sys.argv[1]
	new_repository = sys.argv[2]
	your_email = sys.argv[3]
	your_name = sys.argv[4]
	logs = dump_logs(repository)

	if len(logs) < 50:
		print("Not enough commits in this repository.")
		sys.exit(1)

	print("Dumping commits in patches...")
	dump_commits(repository)

	print("Checking if you made 50 commits in a month...")
	num_commit = find_50commits_month(logs, your_email)
	if num_commit != -1:
		print("You made 50 commits in a month with %d as last commit" % (num_commit))
		offset = compute_offset(logs, num_commit)
		rebuild_repository(repository, new_repository, your_name, your_email, [], offset)
		sys.exit(0)

	print("Searching for a contributor with 50 commits in a month...")
	(contributor, num_commit) = find_contributor_50commits_month(repository, logs)
	if contributor != None:
		print("%s made 50 commits in a month with %d as last commit" % (contributor, num_commit))
		offset = compute_offset(logs, num_commit)
		rebuild_repository(repository, new_repository, your_name, your_email, [contributor], offset)
		sys.exit(0)

	print("Searching for a month with 50 commits...")
	num_commit = find_50commits_month(logs)
	if num_commit != -1:
		print("50 commits in a month were found ending with commit %d" % (num_commit))
		offset = compute_offset(logs, num_commit)
		rebuild_repository(repository, new_repository, your_name, your_email, 'all', offset)
		sys.exit(0)

	#rebuild_repository(repository, new_repository, your_name, your_email, contributors = [], offset = 0)
	print("Unable to find 50 commits in a month.")
	sys.exit(1)
