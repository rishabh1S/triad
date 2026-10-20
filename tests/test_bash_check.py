"""Table-driven tests for bash_check.find_write. Run with: python3 -m unittest discover tests"""

import os
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugins", "triad", "hooks"))
from bash_check import find_write  # noqa: E402

REDIRECT = "output redirection to {}"
IN_PLACE = "`{} -i` (in-place edit)"
CURL = "`curl` writing to a file"
UNPARSEABLE = "a command that could not be parsed (unbalanced quotes)"

# (command, expected reason, or None when the command is allowed)
CASES = [
    # Redirects
    ("echo hi > out.txt", REDIRECT.format("out.txt")),
    ("echo hi >> out.txt", REDIRECT.format("out.txt")),
    ("make &> build.log", REDIRECT.format("build.log")),
    ("echo hi >", REDIRECT.format("a file")),
    ("make 2>&1", None),
    ("echo oops >&2", None),
    ("exec 3>&-", None),
    ("ls > /dev/null", None),
    ("ls >/dev/stdout", None),
    ("ls 2> /dev/stderr", None),
    ("wc -l < files.txt", None),
    ("cat <<EOF", None),
    ('grep x <<< "$v"', None),

    # Segments and command substitution
    ("ls", None),
    ("ls; rm x", "`rm`"),
    ("make && touch done", "`touch`"),
    ("false || mkdir out", "`mkdir`"),
    ("ls | tee list.txt", "`tee`"),
    ("ls\nrm x", "`rm`"),
    ("ls `rm x`", "`rm`"),
    ('echo "$(rm -rf x)"', "`rm`"),
    ('echo "$(git rev-parse HEAD)"', None),

    # Finding the command word
    ("FOO=1 rm x", "`rm`"),
    ("FOO=1", None),
    ("env", None),
    ("if true; then rm x; fi", "`rm`"),
    ("while true; do mv a b; done", "`mv`"),
    ("! rm x", "`rm`"),
    ("{ rm x; }", "`rm`"),
    ("env -i rm x", "`rm`"),
    ("env -u HOME rm x", "`rm`"),
    ("env -C /tmp rm x", "`rm`"),
    ("env -C /tmp ls", None),
    ('env -S "rm x"', "`rm`"),
    ('env -S "ls -l"', None),
    ("command rm x", "`rm`"),
    ("exec rm x", "`rm`"),
    ("exec -a name rm x", "`rm`"),
    ("nohup rm x", "`rm`"),
    ("nohup ls", None),
    ("nice rm x", "`rm`"),
    ("nice -10 rm x", "`rm`"),
    ("nice -n 10 rm x", "`rm`"),
    ("nice -n 10 ls", None),
    ("time rm x", "`rm`"),
    ("timeout 5 rm x", "`rm`"),
    ("timeout 5 ls", None),
    ("timeout -s KILL 5 rm x", "`rm`"),
    ("timeout --signal=KILL 5 rm x", "`rm`"),
    ("timeout -k 1 5 ls", None),
    ("xargs rm", "`rm`"),
    ("xargs -I {} rm {}", "`rm`"),
    ("xargs -P 4 -n 1 rm", "`rm`"),
    ("xargs -0 cat", None),
    ("/bin/rm x", "`rm`"),
    ("./node_modules/.bin/mkdir x", "`mkdir`"),

    # Commands that always write
    ("cp a b", "`cp`"),
    ("ln -s a b", "`ln`"),
    ("chmod +x f", "`chmod`"),
    ("kill 123", "`kill`"),
    ("wget https://x", "`wget`"),
    ("vim f", "`vim`"),
    ("sudo ls", "`sudo`"),

    # In-place edits
    ("sed -i s/a/b/ f", IN_PLACE.format("sed")),
    ("sed -i.bak s/a/b/ f", IN_PLACE.format("sed")),
    ("sed -ni p f", IN_PLACE.format("sed")),
    ("sed --in-place=.bak s/a/b/ f", IN_PLACE.format("sed")),
    ("gsed -i s/a/b/ f", IN_PLACE.format("gsed")),
    ("perl -pi -e s/a/b/ f", IN_PLACE.format("perl")),
    ("sed -n 1p f", None),
    ("sed -E s/a/b/ f", None),
    ("perl -ne print f", None),

    # curl
    ("curl -o f https://x", CURL),
    ("curl -O https://x/f", CURL),
    ("curl -sSLo f https://x", CURL),
    ("curl --output f https://x", CURL),
    ("curl --output=f https://x", CURL),
    ("curl --remote-name https://x/f", CURL),
    ("curl -s https://x", None),
    ("curl -I https://x", None),

    # find
    ("find . -delete", "`find -delete`"),
    ("find . -fprint out.txt", "`find -fprint`"),
    ("find . -exec rm {} ;", "`rm`"),
    ("find . -execdir mv {} x ;", "`mv`"),
    ("find . -ok rm {} ;", "`rm`"),
    ("find . -exec cat {} ;", None),
    ("find . -name '*.py' -print", None),

    # Shells and eval
    ("bash -c 'rm x'", "`rm`"),
    ("sh -lc 'mv a b'", "`mv`"),
    ("zsh -c 'ls'", None),
    ("bash script.sh", None),
    ("eval 'rm x'", "`rm`"),
    ("eval ls", None),

    # git
    ("git", None),
    ("git -C sub commit -m x", "`git commit`"),
    ("git -c core.pager=cat log", None),
    ("git --git-dir=.git log", None),
    ("git --git-dir .git push", "`git push`"),
    ("git --no-pager diff", None),
    ("git blame f", None),
    ("git rev-parse HEAD", None),
    ("git cat-file -p HEAD", None),
    ("git hash-object f", None),
    ("git hash-object -w f", "`git hash-object`"),
    ("git branch", None),
    ("git branch -a -v", None),
    ("git branch new", "`git branch`"),
    ("git tag", None),
    ("git tag -l", None),
    ("git tag v1", "`git tag`"),
    ("git remote", None),
    ("git remote -v", None),
    ("git remote show origin", None),
    ("git remote get-url origin", None),
    ("git remote add x y", "`git remote`"),
    ("git stash list", None),
    ("git stash show", None),
    ("git stash pop", "`git stash`"),
    ("git worktree list", None),
    ("git worktree add ../x", "`git worktree`"),
    ("git notes list", None),
    ("git notes add", "`git notes`"),
    ("git config --get user.name", None),
    ("git config --list", None),
    ("git config user.name x", "`git config`"),
    ("git reflog", None),
    ("git reflog show", None),
    ("git reflog expire --all", "`git reflog`"),
    ("git checkout main", "`git checkout`"),

    # Package managers
    ("npm install", "`npm install`"),
    ("npm ci", "`npm ci`"),
    ("npm test", None),
    ("pnpm add x", "`pnpm add`"),
    ("pnpm test", None),
    ("yarn", "`yarn`"),
    ("yarn add x", "`yarn add`"),
    ("yarn test", None),
    ("bun add x", "`bun add`"),
    ("bun test", None),
    ("pip install x", "`pip install`"),
    ("pip list", None),
    ("pip3 download x", "`pip3 download`"),
    ("pipx install x", "`pipx install`"),
    ("pipx list", None),
    ("uv add x", "`uv add`"),
    ("uv run pytest", None),
    ("uv pip install x", "`pip install`"),
    ("uv pip list", None),
    ("poetry add x", "`poetry add`"),
    ("poetry run pytest", None),
    ("cargo add x", "`cargo add`"),
    ("cargo build", None),
    ("go get x", "`go get`"),
    ("go test ./...", None),
    ("gem install x", "`gem install`"),
    ("gem list", None),
    ("bundle install", "`bundle install`"),
    ("bundle exec rspec", None),
    ("composer require x", "`composer require`"),
    ("composer dump", None),
    ("brew install x", "`brew install`"),
    ("brew list", None),
    ("apt install x", "`apt install`"),
    ("apt-get update", "`apt-get update`"),
    ("apt list", None),
    ("dnf install x", "`dnf install`"),
    ("yum update", "`yum update`"),
    ("apk add x", "`apk add`"),
    ("conda create -n x", "`conda create`"),
    ("conda list", None),
    ("python -m pip install x", "`pip install`"),
    ("python3.12 -m pip install x", "`pip install`"),
    ("python3 -m pip list", None),
    ("python3 -m pytest", None),

    # Parse failures
    ("echo 'unbalanced", UNPARSEABLE),
    ('env -S "rm x', UNPARSEABLE),
]


class FindWrite(unittest.TestCase):
    def test_cases(self):
        for command, expected in CASES:
            with self.subTest(command=command):
                self.assertEqual(find_write(command), expected)


if __name__ == "__main__":
    unittest.main()
