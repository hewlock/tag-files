# tag-cli

CLI to manage file tags. Tags start with `{`; have one or more letters, numbers or `-`; then end with `}`.

Regex: `\{[a-zA-Z0-9-]\}`

Example: `my-file{my-tag-1}{my-tag-2}.txt`

## Usage

```
Usage: tag [OPTIONS] COMMAND [ARGS]...

  tag-cli: filename tags v0.1

  File tags:
    - are in the file name directly before the extension
    - start with '{' and end with '}'
    - consist of letters, numbers and the '-' character

  Examples:
    - myfile{my-tag-1}{my-tag-2}.txt
    - My Title Case File {My-Tag-1}{My-Tag-2}.txt

Options:
  -v, --verbose  Print additional output.
  -d, --debug    Make no changes to the file system.
  --help         Show this message and exit.

Commands:
  add  Add tags to files.
```

### Add

```
Usage: tag add [OPTIONS] TAGS [FILES]...

  Add tags to files.

  TAGS  comma seperated list of tags
  FILES list of files

  Examples:
    - tag add my-tag myfile.txt
    - tag add my-tag-1,my-tag-2 *.txt

Options:
  --help  Show this message and exit.
```
