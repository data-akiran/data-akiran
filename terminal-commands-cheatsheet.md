# Terminal Commands Cheat Sheet

A quick reference for the most common commands used for file navigation, file management, and Git.

---

## 1. File Navigation & Management

### `pwd` — Print Working Directory
Shows the full path of the folder you're currently in.

```bash
pwd
```
Example output:
```
/Users/adityakiran/Documents
```
**Use it to:** confirm where you are before running `mv` or `rm`, so you know exactly which folder a command will affect.

---

### `cd` — Change Directory
Moves you between folders.

```bash
cd Documents            # move into "Documents" (relative to current folder)
cd /Users/adityakiran    # move to an exact/absolute path
cd ..                    # move up one level (to parent folder)
cd ~                     # jump straight to your home folder
cd -                     # jump back to the previous directory you were in
cd                       # typing cd alone also takes you home
```

---

### `ls -ltr` — List Files (detailed, sorted)
Lists files and folders in the current directory.

- `-l` → long format (permissions, owner, size, date modified)
- `-t` → sort by time modified (newest first, by default)
- `-r` → reverse the sort order

Combined, `ls -ltr` shows **oldest files first, newest at the bottom** — handy because the most recently changed file appears right above your next prompt.

```bash
ls -ltr
```
Example output:
```
-rw-r--r--  1 aditya  staff   1024 Jan 10 09:15 old_file.txt
-rw-r--r--  1 aditya  staff   2048 Jan 15 14:30 newer_file.txt
```

---

### `mv` — Move or Rename Files
Used both to move files into another folder and to rename them.

```bash
mv file.txt Documents/                # move file.txt into the Documents folder
mv file.txt Documents/newname.txt     # move AND rename at the same time
mv oldname.txt newname.txt            # rename a file (same folder = just a rename)
mv file.txt ../                       # move file up one directory level
```

**Full example** — moving a photo from Desktop to Pictures:
```bash
cd Desktop
ls -ltr                          # confirm the filename first
mv vacation.jpg ~/Pictures/       # move it into Pictures
```

**Troubleshooting tip:** If you get `mv: rename ... No such file or directory`, either the source file isn't where you think, or the destination folder doesn't exist. Verify both first:
```bash
pwd
find ~ -name "filename.ext"       # locate the real path of the source file
ls ~/path/to/destination/         # confirm the destination folder exists
```
Then move using the full, confirmed path:
```bash
mv /full/path/to/filename.ext ~/path/to/destination/
```

---

### `rm` — Remove (Delete) Files
⚠️ **No trash/undo — this deletes permanently.**

```bash
rm filename.txt          # delete a single file
rm -r foldername         # delete a folder and everything inside it (recursive)
rm -i filename.txt       # ask for confirmation before deleting (safer)
rm *.txt                 # delete all .txt files in current folder (careful with wildcards!)
```

**Safety tip:** Run `ls` on the same pattern first to confirm exactly what would be deleted, since there's no confirmation dialog like Finder's trash.

---

## 2. Copy, Execute, Stop, Edit & Comment in Terminal

### Copying text/output in Terminal
```bash
# Standard macOS copy/paste works in Terminal:
Cmd + C     # copy selected text
Cmd + V     # paste into the command line

# To copy a command's OUTPUT directly to your clipboard (no manual selecting):
pwd | pbcopy              # copies the output of pwd to clipboard
cat file.txt | pbcopy     # copies a file's contents to clipboard

# To paste clipboard contents INTO a file:
pbpaste > newfile.txt
```

### Executing a command
```bash
# Just press Enter/Return after typing a command to run it
ls -ltr    # <- press Enter to execute
```
You can also queue multiple commands on one line:
```bash
cd Documents && ls -ltr    # run second command only if first succeeds
cd Documents; ls -ltr      # run both regardless of whether first succeeds
```

### Stopping a running command
```bash
Ctrl + C     # force-stop (kill) whatever command is currently running
Ctrl + Z     # pause/suspend a running command (can resume later with `fg`)
```
Example: if you accidentally run a command that hangs (like `ping google.com` with no limit), press `Ctrl + C` to stop it immediately.

### Editing a command before running it
```bash
↑ / ↓            # cycle through previous commands (command history)
Ctrl + A          # jump cursor to the beginning of the line
Ctrl + E          # jump cursor to the end of the line
Ctrl + U          # clear the entire line before cursor
Ctrl + K          # clear from cursor to end of line
Ctrl + R          # search backward through command history (type to search, Enter to run)
```

### Adding comments in scripts or the terminal
Anything after a `#` is treated as a comment and ignored when run:
```bash
# This is a comment explaining the next line
ls -ltr    # this comment can also go at the end of a command
```
Useful when writing `.sh` shell scripts to explain what each section does.

---

## 3. Git Commands

### Setup & Basics
```bash
git init                          # initialize a new git repository in current folder
git clone <repo-url>              # copy a remote repository to your local machine
git status                        # show changed/staged/untracked files
```

### Staging & Committing
```bash
git add filename.txt              # stage a specific file for commit
git add .                         # stage all changed files in current folder
git commit -m "message"           # commit staged changes with a message
```

### Branches
```bash
git branch                        # list local branches
git branch new-branch-name        # create a new branch
git checkout branch-name          # switch to a branch
git checkout -b new-branch-name   # create AND switch to a new branch
```

### Syncing with Remote
```bash
git pull                          # fetch and merge changes from remote
git push                          # push local commits to remote
git push origin branch-name       # push a specific branch to remote
git fetch                         # download remote changes without merging
```

### History & Comparison
```bash
git log                           # view commit history
git log --oneline                # compact one-line-per-commit view
git diff                          # show unstaged changes
git diff --staged                 # show staged changes not yet committed
```

### Writing, Editing & Commenting Commit Messages
```bash
git commit -m "message"                     # single-line commit message
git commit                                   # opens default text editor for a longer, multi-line message
git commit -m "Title" -m "Longer description"  # title + body in one command
git commit --amend                           # edit the message of your LAST commit
git commit --amend -m "new message"          # replace last commit's message directly
```
**Notes on the commit message editor:**
- If you run `git commit` with no `-m`, Git opens your default editor (often Vim or Nano) so you can write a longer message.
- Any line starting with `#` inside that editor is a **comment** — Git ignores it and it won't appear in the final commit message. This is used for the auto-generated instructions Git shows you (like "lines starting with '#' will be ignored").
- To save and exit in Vim: press `Esc`, then type `:wq` and hit Enter.
- To exit without saving in Vim: press `Esc`, then type `:q!` and hit Enter.

⚠️ **Only amend commits that haven't been pushed yet** — amending a commit that others have already pulled can cause conflicts for them.

### Undoing Changes
```bash
git restore filename.txt          # discard unstaged changes to a file
git reset filename.txt            # unstage a file (keep the changes)
git revert <commit-hash>          # create a new commit that undoes a previous one
```