"""Find and classify references to the .triad/ folder."""

import os
import re

TRIAD_REF = re.compile(r"(?:^|(?<=[\s/'\"=(]))\.triad(?:/[^\s'\"`;|&()<>]*)?")


def triad_parts(path):
    """Return the path components after the last `.triad`, or None if outside .triad/."""
    parts = os.path.normpath(path).split(os.sep)
    if ".triad" not in parts:
        return None
    return parts[len(parts) - parts[::-1].index(".triad"):]


def triad_file(path):
    """Return the file name directly inside .triad/ (e.g. "plan.md"), "" for the folder
    itself or anything deeper, or None if the path is outside .triad/."""
    rest = triad_parts(path)
    if rest is None:
        return None
    return rest[0] if len(rest) == 1 else ""
