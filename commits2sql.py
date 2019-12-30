#!/usr/bin/env python3

# Copyright (c) 2019 Daniel Jakots
#
# Licensed under the MIT license. See the LICENSE file.

import glob
import os
import sqlite3

SQLITE_PATH = "/tmp/commits.sqlite3"


# rsync -Parv rsync://obsdacvs.cs.toronto.edu/obsdcvs/CVSROOT .
def changelog_list():
    # limit ourselves to recent commits only, syntax changed and I don't care
    # enough to support everything
    for changelog in glob.glob("CVSROOT/ChangeLog.[4-5][0-9]"):
        yield changelog


def changelog_parse(changelog):
    with open(changelog, encoding="iso8859_15") as f:
        content = f.read()
        commits = content.split("CVSROOT:")
        for commit in commits:
            yield commit


def commit_parse(commit):
    if not commit:
        return
    for line in commit.split("\n"):
        if "Module name" in line:
            module = line.split()[-1]
        elif "Changes by" in line:
            commiter = line.split("@")[0].split()[-1]
            date = line[-19:]
    try:
        log_message = commit.split("Log message:")[1]
    except IndexError:
        # it happens when a new directory is added...
        try:
            log_message = commit.split("Log Message:")[1]
        except IndexError:
            # in CVSROOT/ChangeLog.2, the last commit doesn't have a message
            return
    return module, commiter, date, log_message.rstrip().lstrip()


def sqlite3_feed(module, commiter, date, log_message, log_length):
    conn = sqlite3.connect(SQLITE_PATH)
    conn.execute(
        "insert into obsd_commits(module, commiter, date, log_message, log_length) values (?, ?, ?, ?, ?)",
        (module, commiter, date, log_message, log_length),
    )
    conn.commit()
    conn.close()


def sqlite3_init():
    os.unlink(SQLITE_PATH)
    conn = sqlite3.connect(SQLITE_PATH)
    c = conn.cursor()
    c.execute(
        "CREATE TABLE obsd_commits(module varchar, commiter varchar, date varchar, log_message varchar, log_length int);"
    )
    conn.commit()
    conn.close()


def main():
    sqlite3_init()
    for changelog in changelog_list():
        print(changelog)
        for commit in changelog_parse(changelog):
            try:
                module, commiter, date, log_message = commit_parse(commit)
            except TypeError:
                # commit_parse may return nothing
                continue
            sqlite3_feed(module, commiter, date, log_message, len(log_message))


if __name__ == "__main__":
    main()
