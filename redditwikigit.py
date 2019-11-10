import argparse
import logging
import pathlib
import praw
import subprocess
from fastimport.commands import CommitCommand, FileModifyCommand

logger = logging.getLogger('redditwikigit')


def export_wiki(subreddit):
    logger.info("Downloading revision list...")
    revisions = []
    for wikipage in subreddit.wiki:
        for rev in wikipage.revisions():
            if rev:
                logger.debug("  rev: {} {}".format(rev['page'].name,
                                                   rev['id']))
                revisions.append(rev)

    revisions.sort(key=lambda r: r['timestamp'])

    logger.info("Fetching revisions...")
    from_ = None
    for i, rev in enumerate(revisions, 1):
        logger.debug("  rev: {} {}".format(rev['page'].name, rev['id']))
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


def run(subreddit, destination):
    reddit = praw.Reddit(user_agent='redditwikigit')
    subreddit = reddit.subreddit(subreddit)

    subprocess.run(['git', '-C', str(destination), 'init'], check=True)

    p = subprocess.Popen(
        ['git', '-C', str(destination), 'fast-import', '--quiet'],
        stdin=subprocess.PIPE,
    )
    with p.stdin as pipe:
        for command in export_wiki(subreddit):
            pipe.write(bytes(command))
    p.wait()


def main():
    parser = argparse.ArgumentParser(
        description="Mirror a subreddit wiki as a git repository",
    )
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Verbose mode")
    parser.add_argument('subreddit', help="Subreddit to mirror")
    parser.add_argument('destination', nargs='?', help="Destination directory")
    args = parser.parse_args()

    dest_str = args.destination if args.destination else args.subreddit
    dest = pathlib.Path(dest_str)
    dest.mkdir(exist_ok=True)
    if len(list(dest.iterdir())) > 0:
        parser.error("path {} already exists and is not an empty directory"
                     .format(dest_str))

    logging.basicConfig(level=logging.WARNING, format='%(message)s')
    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    logger.info("Mirroring wiki in " + dest_str)

    run(args.subreddit, dest)


if __name__ == '__main__':
    main()
