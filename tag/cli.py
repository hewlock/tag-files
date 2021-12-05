import click
import os
from . import util

VERSION = '0.1.0'

# Options

def opt_all():
    return click.option('--all', '-a', default=False, is_flag=True, help='Include hidden files.')

def opt_count():
    return click.option('--count', '-c', default=False, is_flag=True, help='Display count of matches.')

def opt_debug():
    return click.option('--debug', '-d', default=False, is_flag=True, help='Make no changes to the file system.')

def opt_null():
    return click.option('--null', '-0', default=False, is_flag=True, help='End output lines with NULL (\\0) instead of newline.')

def opt_recursive():
    return click.option('--recursive', '-r', default=False, is_flag=True, help='Include subdirectories recursively.')

def opt_tree(help = 'Print output as tree.'):
    return click.option('--tree', '-t', default=False, is_flag=True, help=help)

def opt_verbose():
    return click.option('--verbose', '-v', default=False, is_flag=True, help='Print additional output.')

def opt_version():
    return click.option('--version', default=False, is_flag=True, help='Print version.')

# Arguments

def arg_path(default='.'):
    return click.argument('path', default=default, type=click.Path(exists=True))

def arg_output():
    return click.argument('output')

def arg_files():
    return click.argument('files', nargs=-1, type=click.Path(exists=True))

def arg_tag():
    return click.argument('tag')

def arg_tags():
    return click.argument('tags')

def arg_old_tag():
    return click.argument('old_tag')

def arg_new_tag():
    return click.argument('new_tag')

# CLI

@click.group(invoke_without_command=True)
@opt_version()
@click.pass_context
def cli(ctx, version):
    '''tag-cli: file name tag manager

    \b
    File tags:
      - are in the file name directly before the extension
      - start with '{' and end with '}'
      - consist of letters, numbers and the '-' character

    \b
    Examples:
      - myfile{my-tag-1}{my-tag-2}.txt
      - My Title Case File {My-Tag-1}{My-Tag-2}.txt
    '''
    if version:
        click.echo(VERSION)
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())

@cli.command('add')
@opt_verbose()
@opt_debug()
@arg_tags()
@arg_files()
def _add(verbose, debug, tags, files):
    '''Add tags to files.

    \b
    TAGS  comma seperated list of tags
    FILES list of files

    \b
    Examples:
      - tag add my-tag myfile.txt
      - tag add my-tag-1,my-tag-2 *.txt
    '''
    tag_list = tags.split(',')
    util.rename_files(verbose, debug, files, lambda tag_set: tag_set.update(tag_list))

@cli.command('clear')
@opt_verbose()
@opt_debug()
@arg_files()
def _clear(verbose, debug, files):
    '''Clear tags from files.

    \b
    FILES list of files

    \b
    Examples:
      - tag clear myfile{my-tag}.txt
      - tag clear *.txt
    '''
    util.rename_files(verbose, debug, files, lambda tag_set: tag_set.clear())

@cli.command('find')
@opt_all()
@opt_null()
@opt_recursive()
@opt_tree()
@arg_tag()
@arg_path()
def _find(all, null, recursive, tree, tag, path):
    '''Find files by tag.

    \b
    TAG  tag to find
    PATH path to search (default .)

    \b
    Examples:
      - tag find -r my-tag path/to/files/
      - tag find my-tag
    '''
    file_list = []
    def handle_file(file):
        if tag in file['tags']:
            file_list.append(file)
    util.find_files(path, recursive, all, handle_file)

    file_list = sorted(map(lambda f: f['original'], file_list))
    output = util.tree_output(path, file_list) if tree else file_list
    delimiter = '\0' if null else '\n'
    click.echo(delimiter.join(output), nl = not null)

@cli.command('remove')
@opt_verbose()
@opt_debug()
@arg_tags()
@arg_files()
def _remove(verbose, debug, tags, files):
    '''Remove tags from files.

    \b
    TAGS  comma seperated list of tags
    FILES list of files

    \b
    Examples:
      - tag remove my-tag myfile{my-tag}.txt
      - tag remove my-tag-1,my-tag-2 *.txt
    '''
    tag_list = tags.split(',')
    util.rename_files(verbose, debug, files, lambda tag_set: tag_set.difference_update(tag_list))

@cli.command('index')
@opt_all()
@opt_debug()
@opt_recursive()
@opt_tree(help = 'Create index with nested tag tree.')
@opt_verbose()
@arg_path(default = None)
@arg_output()
def _index(all, debug, recursive, tree, verbose, path, output):
    '''Index tagged files.

    \b
    PATH   path to search
    OUTPUT path to new index

    \b
    Examples:
      - tag index my-files my-index
      - tag index -r my-files my-index
    '''
    abspath = os.path.abspath(path)

    if os.path.exists(output) and os.listdir(output):
        raise click.ClickException(\
            f'Index directory "{output}" exists with content. '\
            + f'Delete "{output}" or choose a different path.')

    file_list = []
    def handle_file(file):
        if len(file['tags']) > 0:
            file_list.append(file)
    util.find_files(abspath, recursive, all, handle_file)

    index = {}
    for file in file_list:
        for perm in util.permute(sorted(file['tags']), tree):
            filename = os.path.split(file['original'])[1]
            path = os.path.join(output, *perm, filename)
            if path not in index:
                index[path] = []
            index[path].append(file)

    count = 0
    for key in sorted(index.keys()):
        index_len = len(index[key])
        count += index_len
        parent = os.path.split(key)[0]
        if not debug:
            os.makedirs(parent, exist_ok=True)
        if index_len == 1:
            file = index[key][0]
            src = file['original']
            dst = os.path.join(parent, file['filename'])
            if verbose:
                click.echo(f"{dst} -> {src}")
            if not debug:
                os.symlink(src, dst)
        else:
            for file in index[key]:
                path = file['dir'][len(abspath)+1:]
                filename = file['filename']
                if path:
                    split = path.split(os.sep)
                    id = '-'.join(split)
                    base, ext = os.path.splitext(filename)
                    filename = f"{base}-{id}{ext}"
                src = file['original']
                dst = os.path.join(parent, filename)
                if verbose:
                    click.echo(f"{dst} -> {src}")
                if not debug:
                    os.symlink(src, dst)
    if verbose and count > 0:
        message = 'to index' if debug else 'indexed'
        click.echo()
        click.echo(f"{count} files {message}.")


@cli.command('list')
@opt_all()
@opt_count()
@opt_null()
@opt_recursive()
@arg_path()
def _list(all, count, null, recursive, path):
    '''List tags on files.

    \b
    PATH path to search (default .)

    \b
    Examples:
      - tag list -r path/to/files/
      - tag list
    '''
    tags = {}
    def handle_file(file):
        for tag in file['tags']:
            tags[tag] = 1 if not tag in tags else tags[tag] + 1
    util.find_files(path, recursive, all, handle_file)

    output = []
    for tag in sorted(tags.keys()):
        if count:
            output.append(f"{tag}: {tags[tag]}")
        else:
            output.append(tag)
    delimiter = '\0' if null else '\n'
    click.echo(delimiter.join(output), nl = not null)

@cli.command('rename')
@opt_verbose()
@opt_debug()
@arg_old_tag()
@arg_new_tag()
@arg_files()
def _rename(verbose, debug, old_tag, new_tag, files):
    '''Rename a tag on files.

    \b
    OLD_TAG current tag name
    NEW_TAG new tag name
    FILES list of files

    \b
    Examples:
      - tag rename my-tag my-new-tag myfile{my-tag}.txt
      - tag rename my-tag my-new-tag *.txt
    '''
    def tag_handler(tag_set):
        if old_tag in tag_set:
            tag_set.remove(old_tag)
            tag_set.add(new_tag)
    util.rename_files(verbose, debug, files, tag_handler)

@cli.command('set')
@opt_verbose()
@opt_debug()
@arg_tags()
@arg_files()
def _set(verbose, debug, tags, files):
    '''Set tags on files.

    Add and remove tags to ensure each file has the supplied tags and only the supplied tags.

    \b
    TAGS  comma seperated list of tags
    FILES list of files

    \b
    Examples:
      - tag set my-tag myfile{my-tag}.txt
      - tag set my-tag-1,my-tag-2 *.txt
    '''
    tag_list = tags.split(',')
    def tag_handler(tag_set):
        tag_set.clear()
        tag_set.update(tag_list)
    util.rename_files(verbose, debug, files, tag_handler)

@cli.command('sort')
@opt_verbose()
@opt_debug()
@arg_files()
def _sort(verbose, debug, files):
    '''Sort tags on files.

    \b
    FILES list of files

    \b
    Examples:
      - tag sort myfile{my-tag-2}{my-tag-1}.txt
      - tag sort *.txt
    '''
    util.rename_files(verbose, debug, files, lambda tag_set: tag_set)
