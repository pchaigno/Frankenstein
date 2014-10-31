Frankenstein
===

Copy a repository and place 50 of its commits in a month under your name/email address.


### How? ###

* Create a GitHub account.
* Find a good source repository.
* Find a new name for it.
* Create a repository with that name on GitHub.
* Download frankenstein.py (`wget -O frankenstein.py https://bitbucket.org/pchaigno/frankenstein/raw/2500c1ca9d8d30eca804a8c358f88d9b5358c9e2/frankenstein.py`)
* Run `python3 frankenstein.py <Link to the original repository> <New name> <Your email address for GitHub> <Your username on GitHub>`
* Go to the directory created by Frankenstein in the previous step (New name)
* Run `git remote add origin https://<Your username on GitHub>@github.com/<Your username on GitHub>/<New name>`
* Run `git push origin master`
* Bob's your uncle!


### How to report a bug? ###

* Send an email at paul.chaignon@gmail.com
* or open an issue on BitBucket.