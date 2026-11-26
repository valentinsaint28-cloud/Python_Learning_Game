"""Checks the player's code.

Order of the checks:  empty -> syntax -> run safely (timeout) -> output -> required constructs

Usage:
    checker = CodeChecker()
    result = checker.run(code)           # "Run" button: just execute and show the output
    result = checker.check(code, task)   # "Check" button: also compares with the task

`task` is one entry of tasks.json. It uses:
    "expected_output": "14"
    "checks": ["operator:*", "variable:total"]     (optional)
"""
import ast
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional

TIMEOUT_SECONDS = 2.0
MAX_OUTPUT_CHARS = 5000

# Only these builtins exist for the player's code (no open, no __import__, no eval ...)
ALLOWED_BUILTINS = [
    "print", "range", "len", "int", "float", "str", "bool", "list", "dict", "tuple", "set",
    "abs", "min", "max", "sum", "round", "sorted", "reversed", "enumerate", "zip",
    "map", "filter", "any", "all", "pow", "divmod", "chr", "ord", "repr", "format",
    "type", "isinstance", "object", "__build_class__",
    "Exception", "ValueError", "TypeError", "ZeroDivisionError", "IndexError", "KeyError",
]

# Program that runs in a separate process. The code arrives through stdin.
_RUNNER = '''
import sys, json, builtins
sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")
ALLOWED = __ALLOWED__
LIMIT = __LIMIT__
real_stdout = sys.stdout


class Limited:
    """Stops programs that print endlessly."""
    def __init__(self):
        self.count = 0

    def write(self, text):
        self.count += len(text)
        if self.count > LIMIT:
            raise RuntimeError("Too much output")
        return real_stdout.write(text)

    def flush(self):
        real_stdout.flush()


code = sys.stdin.read()
safe = {name: getattr(builtins, name) for name in ALLOWED if hasattr(builtins, name)}
sys.stdout = Limited()
try:
    exec(compile(code, "<player>", "exec"), {"__builtins__": safe, "__name__": "__main__"})
except BaseException as exc:
    line = exc.lineno if isinstance(exc, SyntaxError) else None
    tb = exc.__traceback__
    while tb:
        if tb.tb_frame.f_code.co_filename == "<player>":
            line = tb.tb_lineno
        tb = tb.tb_next
    sys.stdout = real_stdout
    sys.stderr.write(json.dumps({"type": type(exc).__name__, "message": str(exc), "line": line}))
    sys.exit(1)
'''


@dataclass
class CheckResult:
    ok: bool
    stage: str          # empty | syntax | timeout | runtime | output | requirement | ran | passed
    message: str        # friendly text to show to the player
    output: str = ""    # what the code printed
    expected: str = ""  # what the task expects (only set when the output was compared)
    line: Optional[int] = None  # line of the error, if known


# ---------------------------------------------------------------- friendly messages
def friendly_syntax_message(error: SyntaxError) -> str:
    msg = (error.msg or "").lower()
    if "unterminated string" in msg or "eol while scanning" in msg:
        return "A quotation mark is missing. Every opening quote needs a closing one."
    if "never closed" in msg or "unmatched" in msg:
        return "A bracket is missing or there is one too many. Check your parentheses ( )."
    if "expected ':'" in msg:
        return "Don't forget the colon ':' at the end of this line."
    if "expected an indented block" in msg:
        return "This line needs to be indented. Add 4 spaces at the start."
    if "unexpected indent" in msg or "unindent" in msg:
        return "The indentation looks wrong. Lines in the same block need the same number of spaces."
    return "Python can't understand this line. Check the spelling, quotes and brackets."


def friendly_runtime_message(kind: str, message: str) -> str:
    if kind == "NameError":
        match = re.search(r"name '(.+)' is not defined", message)
        name = match.group(1) if match else "that name"
        return f"Python doesn't know '{name}'. Check the spelling, or create it before you use it."
    if kind == "ImportError" or "__import__" in message:
        return "Imports are not allowed in this game."
    if kind == "ZeroDivisionError":
        return "You can't divide by zero."
    if kind == "TypeError":
        return f"These values don't fit together (for example text and numbers). {message}"
    if kind == "IndexError":
        return "That position doesn't exist in the list."
    if kind == "RuntimeError" and "Too much output" in message:
        return "Your code prints too much. Is a loop running forever?"
    return f"{kind}: {message}"


# ---------------------------------------------------------------- requirements (AST)
OPERATORS = {"+": ast.Add, "-": ast.Sub, "*": ast.Mult, "/": ast.Div,
             "//": ast.FloorDiv, "%": ast.Mod, "**": ast.Pow}
COMPARISONS = {"==": ast.Eq, "!=": ast.NotEq, "<": ast.Lt, "<=": ast.LtE,
               ">": ast.Gt, ">=": ast.GtE}


def _assigns(node, name):
    if isinstance(node, ast.Assign):
        targets = node.targets
    elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
        targets = [node.target]
    else:
        return False
    return any(isinstance(t, ast.Name) and t.id == name
               for target in targets for t in ast.walk(target))


# kind -> function(node, argument) that is True when this node satisfies the requirement
_PREDICATES = {
    "for_loop": lambda n, a: isinstance(n, ast.For),
    "while_loop": lambda n, a: isinstance(n, ast.While),
    "if": lambda n, a: isinstance(n, ast.If),
    "else": lambda n, a: isinstance(n, ast.If) and bool(n.orelse),
    "function_def": lambda n, a: isinstance(n, ast.FunctionDef),
    "return": lambda n, a: isinstance(n, ast.Return),
    "list": lambda n, a: isinstance(n, (ast.List, ast.ListComp)),
    "dict": lambda n, a: isinstance(n, ast.Dict),
    "compare": lambda n, a: isinstance(n, ast.Compare)
        and (not a or any(isinstance(op, COMPARISONS[a]) for op in n.ops)),
    "operator": lambda n, a: isinstance(n, (ast.BinOp, ast.AugAssign)) and isinstance(n.op, OPERATORS[a]),
    "call": lambda n, a: isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == a,
    "variable": lambda n, a: _assigns(n, a),
}

_NEEDS_ARGUMENT = {"operator", "call", "variable"}

_MESSAGES = {
    "for_loop": "Use a for loop to solve this task.",
    "while_loop": "Use a while loop to solve this task.",
    "if": "Use an if statement to solve this task.",
    "else": "Use if together with else to solve this task.",
    "function_def": "Define a function with def.",
    "return": "Your function should use return.",
    "list": "Use a list.",
    "dict": "Use a dictionary.",
    "compare": "Use a comparison (like >= or ==).",
}


def parse_requirement(spec):
    """'operator:*'  or  {"check": "operator:*", "message": "..."}  ->  (kind, argument, custom_message)"""
    custom = None
    if isinstance(spec, dict):
        custom = spec.get("message")
        spec = spec["check"]
    kind, _, arg = spec.partition(":")
    if kind not in _PREDICATES:
        raise ValueError(f"Unknown requirement '{spec}' in tasks.json")
    if kind in _NEEDS_ARGUMENT and not arg:
        raise ValueError(f"Requirement '{kind}' needs an argument, e.g. '{kind}:name'")
    if kind == "operator" and arg not in OPERATORS:
        raise ValueError(f"Unknown operator '{arg}' in tasks.json")
    if kind == "compare" and arg and arg not in COMPARISONS:
        raise ValueError(f"Unknown comparison '{arg}' in tasks.json")
    return kind, arg, custom


def requirement_message(kind, arg):
    if kind == "operator":
        return f"Use the {arg} operator in your calculation."
    if kind == "call":
        return f"Use {arg}() in your solution."
    if kind == "variable":
        return f"Create a variable called {arg}."
    if kind == "compare" and arg:
        return f"Use the {arg} comparison."
    return _MESSAGES[kind]


def validate_tasks(tasks):
    """Call once after loading tasks.json to find typos in the "checks" lists."""
    for task in tasks.values() if isinstance(tasks, dict) else tasks:
        for spec in task.get("checks", []):
            parse_requirement(spec)


# ---------------------------------------------------------------- output comparison
def normalize(text):
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return "\n".join(line.rstrip() for line in lines).strip()


def output_hint(actual, expected):
    a, e = normalize(actual), normalize(expected)
    if not a:
        return "Your code printed nothing. Did you use print()?"
    if a.lower() == e.lower():
        return "Almost! Check the upper and lower case letters."
    if a.replace(" ", "") == e.replace(" ", ""):
        return "Almost! Check the spaces."
    if len(a.splitlines()) != len(e.splitlines()):
        return (f"The output should have {len(e.splitlines())} line(s), "
                f"but yours has {len(a.splitlines())}.")
    return "The output doesn't match yet. Compare it with the goal of the task."


# ---------------------------------------------------------------- the checker
class CodeChecker:
    def __init__(self, timeout=TIMEOUT_SECONDS):
        self.timeout = timeout
        self._runner = (_RUNNER
                        .replace("__ALLOWED__", repr(ALLOWED_BUILTINS))
                        .replace("__LIMIT__", str(MAX_OUTPUT_CHARS)))

    def run(self, code):
        """Syntax check + safe execution. ok=True (stage 'ran') means it ran without errors."""
        if not code.strip():
            return CheckResult(False, "empty", "Write some code first.")
        try:
            ast.parse(code)
        except SyntaxError as error:
            return CheckResult(False, "syntax", friendly_syntax_message(error), line=error.lineno)

        try:
            proc = subprocess.run(
                [sys.executable, "-I", "-c", self._runner],
                input=code, capture_output=True, text=True, encoding="utf-8",
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            return CheckResult(False, "timeout",
                               "Your code ran for too long. Is there a loop that never ends?")

        if proc.returncode != 0:
            try:
                info = json.loads(proc.stderr)
            except ValueError:
                return CheckResult(False, "runtime", "Something went wrong while running your code.",
                                   output=proc.stdout)
            if info["type"] in ("SyntaxError", "IndentationError"):
                return CheckResult(False, "syntax", "Python can't understand your code. "
                                   "Check the spelling, quotes and indentation.", line=info["line"])
            return CheckResult(False, "runtime",
                               friendly_runtime_message(info["type"], info["message"]),
                               output=proc.stdout, line=info["line"])

        return CheckResult(True, "ran", "", output=proc.stdout)

    def check(self, code, task):
        """Run the code, then compare with the task's expected output and required constructs."""
        result = self.run(code)
        if not result.ok:
            return result

        expected = task.get("expected_output", "")
        if normalize(result.output) != normalize(expected):
            return CheckResult(False, "output", output_hint(result.output, expected),
                               output=result.output, expected=expected)

        tree = ast.parse(code)
        for spec in task.get("checks", []):
            kind, arg, custom = parse_requirement(spec)
            if not any(_PREDICATES[kind](node, arg) for node in ast.walk(tree)):
                message = custom or requirement_message(kind, arg)
                return CheckResult(False, "requirement",
                                   f"Your output is correct, but the task asks for more. {message}",
                                   output=result.output, expected=expected)

        return CheckResult(True, "passed", "Well done!", output=result.output, expected=expected)
