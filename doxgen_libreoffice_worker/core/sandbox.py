"""Safe rendering of untrusted appy.pod templates.

Templates come from API users. Their expressions run through RestrictedPython, and they cannot
import documents, images or sub-templates from a path or a URL.
"""

import builtins

from appy.pod import PodError
from appy.pod.renderer import Renderer
from appy.pod.restricted import Evaluator
from RestrictedPython import limited_builtins, safe_builtins
from RestrictedPython.Eval import default_guarded_getitem, default_guarded_getiter
from RestrictedPython.Guards import (
    full_write_guard,
    guarded_iter_unpack_sequence,
    guarded_unpack_sequence,
    safer_getattr,
)
from RestrictedPython.PrintCollector import PrintCollector

# Builtins that only work on data. RestrictedPython checks attribute and item access.
EXTRA_BUILTINS = (
    "all",
    "any",
    "dict",
    "enumerate",
    "filter",
    "frozenset",
    "map",
    "max",
    "min",
    "reversed",
    "set",
    "sum",
)


def _restricted_globals():
    template_builtins = dict(safe_builtins)
    template_builtins.update(limited_builtins)
    template_builtins.update({name: getattr(builtins, name) for name in EXTRA_BUILTINS})
    return {
        "__builtins__": template_builtins,
        "_getattr_": safer_getattr,
        "_getitem_": default_guarded_getitem,
        "_getiter_": default_guarded_getiter,
        "_iter_unpack_sequence_": guarded_iter_unpack_sequence,
        "_unpack_sequence_": guarded_unpack_sequence,
        "_write_": full_write_guard,
        "_print_": PrintCollector,
    }


def make_evaluator():
    # appy adds these entries to the context after the user's data, so the data cannot replace them.
    return Evaluator(custom=_restricted_globals())


class SafeRenderer(Renderer):
    """A Renderer that refuses to read files or URLs named in a template."""

    def __init__(self, *args, **kwargs):
        kwargs["evaluator"] = make_evaluator()
        super().__init__(*args, **kwargs)

    def importDocument(self, content=None, at=None, *args, **kwargs):
        # xhtml() also comes here for <img src="...">.
        if at is not None:
            raise PodError("Templates cannot import a document or an image from a path or a URL.")
        return super().importDocument(content, None, *args, **kwargs)

    def importPod(self, content=None, at=None, *args, **kwargs):
        raise PodError("Templates cannot import another template.")
