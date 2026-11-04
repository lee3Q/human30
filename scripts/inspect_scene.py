#!/usr/bin/env python3
"""Read one explicitly selected stored scene file. Never run a simulation."""
import argparse
import os
import stat
import sys

MAX_BYTES = 8 * 1024 * 1024


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse errors can echo arbitrary unknown arguments and controls.
        self.exit(2, 'error: invalid arguments; use --help for supported syntax\n')


def read_saved(scene, channel, character):
    if os.name != 'posix' or not all(hasattr(os, flag) for flag in ('O_NOFOLLOW', 'O_DIRECTORY')) or os.open not in os.supports_dir_fd:
        raise ValueError('safe directory-relative reading is unsupported on this platform')
    if not scene:
        raise ValueError('scene directory must be explicitly supplied')
    parts = scene.split('/')
    if '..' in parts:
        raise ValueError('parent-directory components are not supported')
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    directory = os.open('/' if scene.startswith('/') else '.', flags)
    try:
        for part in parts:
            if part in ('', '.'):
                continue
            child = os.open(part, flags, dir_fd=directory)
            os.close(directory)
            directory = child
        if channel == 'surface':
            name = 'surface.md'
        else:
            child = os.open(channel, flags, dir_fd=directory)
            os.close(directory)
            directory = child
            name = f'{character:02d}.md'
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                raise ValueError('saved observation is not a regular file')
            if info.st_size > MAX_BYTES:
                raise ValueError('saved observation exceeds the 8 MiB read limit')
            with os.fdopen(fd, 'rb', closefd=False) as stream:
                raw = stream.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError('saved observation exceeds the 8 MiB read limit')
        finally:
            os.close(fd)
    finally:
        os.close(directory)
    text = raw.decode('utf-8')
    for i, char in enumerate(text):
        code = ord(char)
        if (code < 32 and char not in '\t\n') or 127 <= code <= 159 or code in (0x061c, 0x200e, 0x200f) or 0x202a <= code <= 0x202e or 0x2066 <= code <= 0x2069:
            raise ValueError(f'unsupported control character at character offset {i}')
    return raw


def main(argv=None):
    parser = SafeParser(description='Read a saved scene file only; no simulation, generation, memory append or latest-scene selection.')
    parser.add_argument('scene', help='explicit scene directory; no symlink or .. components')
    parser.add_argument('channel', choices=('surface', 'interior', 'phone', 'subconscious'))
    parser.add_argument('character', nargs='?', help='character ID 1-30, required except for surface')
    args = parser.parse_args(argv)
    character = None
    if any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in args.scene):
        parser.error('scene path contains unsupported control characters')
    if args.channel == 'surface':
        if args.character is not None:
            parser.error('surface does not accept a character ID')
    else:
        if args.character is None or len(args.character) not in (1, 2) or not args.character.isascii() or not args.character.isdecimal() or not 1 <= int(args.character) <= 30:
            parser.error('character ID must be an ASCII integer from 1 through 30')
        character = int(args.character)
    try:
        raw = read_saved(args.scene, args.channel, character)
    except FileNotFoundError:
        print('error: no saved observation at the selected scene/channel; this does not establish that no activity occurred', file=sys.stderr)
        return 2
    except (OSError, UnicodeError, ValueError):
        # Never echo a path, file content or exception string into the terminal.
        print('error: cannot read saved observation (unsafe path, permissions, unsupported platform, nonregular file, 8 MiB limit, invalid UTF-8 or control characters)', file=sys.stderr)
        return 2
    try:
        # Bypass buffered stdout: failed writes must not be retried at shutdown.
        view = memoryview(raw)
        while view:
            written = os.write(sys.stdout.fileno(), view)
            if written <= 0:
                raise OSError('stdout made no progress')
            view = view[written:]
    except (BrokenPipeError, OSError):
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
