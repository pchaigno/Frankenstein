#!/usr/bin/env python3
import sys
import json
import os
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


def dump_commits(repository):
	os.chdir(repository)
	json_data = open("logs.json")
	logs = json.load(json_data)
	json_data.close()

	os.system("git show --binary %s > 0.patch" % (logs[0]['hash']))
	for i in range(1, len(logs)):
		os.system("git diff --binary %s %s > %d.patch" % (logs[i-1]['hash'], logs[i]['hash'], i))


def rebuild_repository(dump_folder, repository):
	os.system("mkdir %s" % (repository))
	os.chdir(repository)

	json_data = open("../%s/logs.json" % (dump_folder))
	logs = json.load(json_data)
	json_data.close()

	os.system("git init")
	for i in range(0, len(logs)):
		log = logs[i]
		os.system("git apply ../%s/%d.patch" % (dump_folder, i))
		os.system("git add --all .")
		os.environ["GIT_COMMITTER_NAME"] = log['committer']
		os.environ["GIT_COMMITTER_EMAIL"] = log['committer-email']
		os.environ["GIT_COMMITTER_DATE"] = str(log['committer-date'])
		os.system("""git commit -m "%s" --author="%s <%s>" --date=%d""" % (log['message'], log['author'], log['author-email'], log['author-date']))

	os.chdir('..')


def get_contributors(repository):
	os.chdir(repository)
	process1 = subprocess.Popen(('git', 'log', '--format=%ae'), stdout=subprocess.PIPE)
	process2 = subprocess.Popen(('sort', '-u'), stdin=process1.stdout, stdout=subprocess.PIPE)
	contributors = process2.stdout.read().decode('utf-8').split("\n")
	os.chdir('..')
	return contributors


def check_repository(repository, author):
	json_data = open("%s/logs.json" % (repository))
	logs = json.load(json_data)
	json_data.close()

	if len(logs) < 50:
		print("Not enough commits in this repository.")

	for i in range(len(logs)-1, 50, -1):
		nb_commits = 0
		for j in range(i-1, 0, -1):
			if logs[j]['author-email'] == author:
				period = logs[i]['author-date'] - logs[j]['author-date']
				if period > 30 * 24 * 3600:
					break
				if nb_commits >= 50:
					print("Match found for %s! (n%d => -%d)" % (author, i, len(logs) - i))
					return i
				nb_commits += 1

	return -1


if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("Usage: frankenstein.py <repository>")
		sys.exit(2)

	repository = sys.argv[1]
	dump_logs(repository)
	contributors = get_contributors(repository)
	for contributor in contributors:
		check_repository(repository, contributor)
