import praw
from fastimport.commands import CommitCommand, FileModifyCommand


def export_wiki(subreddit):
    revisions = []
    for wikipage in subreddit.wiki:
        for wikirev in wikipage.revisions():
            if wikirev:
                revisions.append(wikirev)

    revisions.sort(key=lambda r: r['timestamp'])

    from_ = None
    for i, rev in enumerate(revisions, 1):
        import sys
        print(rev, file=sys.stderr)
        author = rev['author'].name.encode() if rev['author'] else b'null'
        path = rev['page'].name + '.md'
        message = rev['reason'] or 'Update ' + rev['page'].name
        yield CommitCommand(
            ref=b'refs/heads/master',
            mark=i,
            author=None,
            committer=(
                author,
                author.lower() + b'@users.reddit.com',
                rev['timestamp'],
                0
            ),
            message=message.encode(),
            from_=from_,
            merges=None,
            file_iter=[
                FileModifyCommand(
                    path=path.encode(),
                    mode=0o644,
                    dataref=None,
                    data=rev['page'].content_md.encode(),
                )
            ]
        )
        from_ = b':' + str(i).encode()


def main():
    reddit = praw.Reddit(user_agent='redditwikigit')
    subreddit = reddit.subreddit('economics')  # FIXME: parameter
    for command in export_wiki(subreddit):
        print(command)


if __name__ == '__main__':
    main()
