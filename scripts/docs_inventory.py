"""Static source inventory shared by the documentation build tools.

The inventory uses Python's AST instead of importing :mod:`vllm_mlx`. This is
important because the documentation build runs on Linux while the runtime
package depends on Apple Silicon and MLX.
"""

from __future__ import annotations

import ast
import html
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

REPOSITORY_URL = "https://github.com/waybarrios/vllm-mlx"
SOURCE_BRANCH = "gh-pages"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Parameter:
    """One explicit callable input reconstructed from the Python AST."""

    name: str
    kind: str
    annotation: str
    default: str
    required: bool
    description: str

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation of the parameter."""

        return asdict(self)


@dataclass(frozen=True)
class Symbol:
    """A class, function, method, or nested definition found in source code."""

    name: str
    qualname: str
    full_name: str
    kind: str
    signature: str
    parameters: tuple[Parameter, ...]
    return_annotation: str
    docstring: str
    summary: str
    implementation: str
    documented: bool
    public: bool
    addressable: bool
    line: int
    end_line: int
    source_url: str
    decorators: tuple[str, ...]
    calls: tuple[str, ...]
    state_reads: tuple[str, ...]
    state_writes: tuple[str, ...]
    raises: tuple[str, ...]
    return_expressions: tuple[str, ...]
    awaits: bool
    yields: bool

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation of the symbol."""

        return asdict(self)


@dataclass(frozen=True)
class Module:
    """Documentation metadata for one tracked Python module."""

    name: str
    path: str
    page_path: str
    docstring: str
    summary: str
    line_count: int
    source_url: str
    members: tuple[str, ...]
    symbols: tuple[Symbol, ...]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation of the module."""

        payload = asdict(self)
        payload["symbols"] = [symbol.to_dict() for symbol in self.symbols]
        return payload


@dataclass(frozen=True)
class CLIOption:
    """One argparse option declaration found in executable source."""

    context: str
    receiver: str
    flags: tuple[str, ...]
    destination: str
    description: str
    default: str
    required: bool
    choices: str
    action: str
    path: str
    line: int
    end_line: int
    source_url: str

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation of the option."""

        return asdict(self)


def _tracked_python_files(
    root: Path, source_roots: tuple[str, ...] = ("vllm_mlx",)
) -> list[Path]:
    """Return tracked modules under selected roots, with a filesystem fallback."""

    completed = subprocess.run(
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            *source_roots,
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0:
        paths = [root / line for line in completed.stdout.splitlines()]
        tracked = [
            path
            for path in paths
            if path.suffix == ".py" and path.relative_to(root).parts[0] in source_roots
        ]
        if tracked:
            return sorted(tracked)
    return sorted(
        path
        for source_root in source_roots
        for path in (root / source_root).rglob("*.py")
    )


def module_name_for_path(path: Path, root: Path = REPOSITORY_ROOT) -> str:
    """Convert a package source path into its importable dotted module name."""

    relative = path.relative_to(root).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def page_path_for_module(path: Path, root: Path = REPOSITORY_ROOT) -> Path:
    """Return the generated documentation path for a package source file."""

    relative = path.relative_to(root).with_suffix(".md")
    if relative.name == "__init__.md":
        relative = relative.with_name("index.md")
    section = "api" if relative.parts[0] == "vllm_mlx" else "source"
    return Path("reference") / section / relative


def _first_sentence(docstring: str) -> str:
    """Return a compact first sentence or line from a docstring."""

    text = " ".join(docstring.strip().split())
    if not text:
        return ""
    match = re.search(r"(?<=[.!?])\s", text)
    return text[: match.start()] if match else text


def _parameter_descriptions(docstring: str) -> dict[str, str]:
    """Extract Google, NumPy, and Sphinx parameter descriptions."""

    descriptions: dict[str, str] = {}
    lines = docstring.splitlines()

    for line in lines:
        sphinx_match = re.match(
            r"\s*:param(?:\s+[^: ]+)?\s+([*]{0,2}[A-Za-z_]\w*)\s*:\s*(.*)",
            line,
        )
        if sphinx_match:
            descriptions[sphinx_match.group(1).lstrip("*")] = sphinx_match.group(
                2
            ).strip()

    section_start = next(
        (
            index + 1
            for index, line in enumerate(lines)
            if line.strip() in {"Args:", "Arguments:", "Parameters:"}
        ),
        None,
    )
    if section_start is not None:
        current_names: list[str] = []
        for line in lines[section_start:]:
            stripped = line.strip()
            if not stripped:
                continue
            if not line[:1].isspace() or (
                stripped.endswith(":")
                and not re.match(r"[*]{0,2}[A-Za-z_]\w*\s*:", stripped)
            ):
                break
            item = re.match(
                r"([*]{0,2}[A-Za-z_]\w*(?:\s*,\s*[*]{0,2}[A-Za-z_]\w*)*)"
                r"(?:\s*\([^)]*\))?\s*:\s*(.*)",
                stripped,
            )
            if item:
                current_names = [
                    name.strip().lstrip("*") for name in item.group(1).split(",")
                ]
                for name in current_names:
                    descriptions[name] = item.group(2).strip()
            elif current_names:
                for name in current_names:
                    descriptions[name] = " ".join(
                        part for part in (descriptions[name], stripped) if part
                    )

    for index, line in enumerate(lines[:-1]):
        if line.strip() != "Parameters" or not set(lines[index + 1].strip()) <= {"-"}:
            continue
        current_names = []
        for item_line in lines[index + 2 :]:
            stripped = item_line.strip()
            if not stripped:
                continue
            if not item_line[:1].isspace() and re.match(r"^[A-Za-z].*:$", stripped):
                break
            item = re.match(
                r"([*]{0,2}[A-Za-z_]\w*(?:\s*,\s*[*]{0,2}[A-Za-z_]\w*)*)" r"\s*:\s*.+",
                stripped,
            )
            if item and not item_line[:1].isspace():
                current_names = [
                    name.strip().lstrip("*") for name in item.group(1).split(",")
                ]
                for name in current_names:
                    descriptions.setdefault(name, "")
            elif current_names:
                for name in current_names:
                    descriptions[name] = " ".join(
                        part for part in (descriptions[name], stripped) if part
                    )
        break

    return descriptions


def _function_parameters(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    docstring: str,
) -> tuple[Parameter, ...]:
    """Return the callable inputs, annotations, defaults, and descriptions."""

    descriptions = _parameter_descriptions(docstring)
    positional = [*node.args.posonlyargs, *node.args.args]
    positional_defaults: list[ast.AST | None] = [None] * (
        len(positional) - len(node.args.defaults)
    ) + list(node.args.defaults)
    parameters: list[Parameter] = []

    def append_parameter(
        argument: ast.arg,
        *,
        kind: str,
        default_node: ast.AST | None,
        required: bool,
        prefix: str = "",
    ) -> None:
        if argument.arg in {"self", "cls"}:
            return
        default = _short_expression(default_node) if default_node is not None else ""
        description = descriptions.get(argument.arg, "")
        if not description:
            if prefix:
                description = f"Additional {kind} inputs accepted by this callable."
            elif required:
                description = f"Required {kind} input."
            else:
                description = f"Optional {kind} input; defaults to `{default}`."
        parameters.append(
            Parameter(
                name=f"{prefix}{argument.arg}",
                kind=kind,
                annotation=(
                    _short_expression(argument.annotation)
                    if argument.annotation is not None
                    else "not annotated"
                ),
                default=default,
                required=required,
                description=description,
            )
        )

    positional_only_count = len(node.args.posonlyargs)
    for index, (argument, default_node) in enumerate(
        zip(positional, positional_defaults)
    ):
        append_parameter(
            argument,
            kind=(
                "positional-only"
                if index < positional_only_count
                else "positional or keyword"
            ),
            default_node=default_node,
            required=default_node is None,
        )
    if node.args.vararg is not None:
        append_parameter(
            node.args.vararg,
            kind="variadic positional",
            default_node=None,
            required=False,
            prefix="*",
        )
    for argument, default_node in zip(node.args.kwonlyargs, node.args.kw_defaults):
        append_parameter(
            argument,
            kind="keyword-only",
            default_node=default_node,
            required=default_node is None,
        )
    if node.args.kwarg is not None:
        append_parameter(
            node.args.kwarg,
            kind="variadic keyword",
            default_node=None,
            required=False,
            prefix="**",
        )
    return tuple(parameters)


def _class_parameters(node: ast.ClassDef, docstring: str) -> tuple[Parameter, ...]:
    """Return constructor inputs from ``__init__`` or declarative fields."""

    initializer = next(
        (
            child
            for child in node.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            and child.name == "__init__"
        ),
        None,
    )
    if initializer is not None:
        initializer_docstring = ast.get_docstring(initializer, clean=True) or ""
        return _function_parameters(
            initializer,
            "\n".join(part for part in (docstring, initializer_docstring) if part),
        )

    decorators = {ast.unparse(item).split("(", 1)[0] for item in node.decorator_list}
    bases = {ast.unparse(base).rsplit(".", 1)[-1] for base in node.bases}
    if not (
        decorators & {"dataclass", "dataclasses.dataclass"}
        or bases & {"BaseModel", "TypedDict"}
    ):
        return ()

    descriptions = _parameter_descriptions(docstring)
    parameters: list[Parameter] = []
    for child in node.body:
        if not isinstance(child, ast.AnnAssign) or not isinstance(
            child.target, ast.Name
        ):
            continue
        name = child.target.id
        default = _short_expression(child.value) if child.value is not None else ""
        required = child.value is None
        parameters.append(
            Parameter(
                name=name,
                kind="field",
                annotation=_short_expression(child.annotation),
                default=default,
                required=required,
                description=descriptions.get(name)
                or (
                    "Required constructor field."
                    if required
                    else f"Optional constructor field; defaults to `{default}`."
                ),
            )
        )
    return tuple(parameters)


def _owned_nodes(node: ast.AST) -> Iterable[ast.AST]:
    """Walk implementation nodes without attributing nested bodies to parents."""

    body = getattr(node, "body", ())
    stack = list(reversed(body))
    while stack:
        child = stack.pop()
        yield child
        if isinstance(
            child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
        ):
            continue
        stack.extend(reversed(list(ast.iter_child_nodes(child))))


def _ordered_unique(values: Iterable[str]) -> tuple[str, ...]:
    """Return non-empty strings once while preserving their source order."""

    return tuple(dict.fromkeys(value for value in values if value))


def _short_expression(node: ast.AST | None, *, limit: int = 120) -> str:
    """Render an AST expression without allowing one fact to dominate output."""

    if node is None:
        return "None"
    value = " ".join(ast.unparse(node).split())
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _attribute_name(node: ast.Attribute) -> str:
    """Return tracked ``self`` or ``cls`` attribute access, if applicable."""

    parts = [node.attr]
    value = node.value
    while isinstance(value, ast.Attribute):
        parts.append(value.attr)
        value = value.value
    if isinstance(value, ast.Name) and value.id in {"self", "cls"}:
        parts.append(value.id)
        return ".".join(reversed(parts))
    return ""


def _implementation_facts(
    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    kind: str,
    qualname: str,
) -> dict[str, object]:
    """Extract conservative behavioral facts from one definition's own body."""

    decorators = _ordered_unique(ast.unparse(item) for item in node.decorator_list)
    if isinstance(node, ast.ClassDef):
        direct_members = [
            child.name
            for child in node.body
            if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        bases = [ast.unparse(base) for base in node.bases]
        clauses = []
        if bases:
            clauses.append("derives from " + ", ".join(f"`{base}`" for base in bases))
        clauses.append(f"declares {len(direct_members)} direct member(s)")
        implementation = f"{kind.title()} `{qualname}` " + " and ".join(clauses) + "."
        return {
            "implementation": implementation,
            "decorators": decorators,
            "calls": (),
            "state_reads": (),
            "state_writes": (),
            "raises": (),
            "return_expressions": (),
            "awaits": False,
            "yields": False,
        }

    owned = list(_owned_nodes(node))
    calls = _ordered_unique(
        _short_expression(item.func) for item in owned if isinstance(item, ast.Call)
    )
    state_reads = _ordered_unique(
        _attribute_name(item)
        for item in owned
        if isinstance(item, ast.Attribute) and isinstance(item.ctx, ast.Load)
    )
    state_writes = _ordered_unique(
        _attribute_name(item)
        for item in owned
        if isinstance(item, ast.Attribute) and isinstance(item.ctx, ast.Store)
    )
    raises = _ordered_unique(
        (
            _short_expression(item.exc.func)
            if isinstance(item.exc, ast.Call)
            else _short_expression(item.exc)
        )
        for item in owned
        if isinstance(item, ast.Raise) and item.exc is not None
    )
    return_expressions = _ordered_unique(
        _short_expression(item.value) for item in owned if isinstance(item, ast.Return)
    )
    awaits = any(isinstance(item, ast.Await) for item in owned)
    yields = any(isinstance(item, (ast.Yield, ast.YieldFrom)) for item in owned)

    clauses: list[str] = []
    if state_writes:
        clauses.append("updates " + ", ".join(f"`{name}`" for name in state_writes[:4]))
    if calls:
        clauses.append("calls " + ", ".join(f"`{name}`" for name in calls[:4]))
    if awaits:
        clauses.append("awaits asynchronous work")
    if yields:
        clauses.append("yields values incrementally")
    if raises:
        clauses.append("can raise " + ", ".join(f"`{name}`" for name in raises[:4]))
    if return_expressions:
        if len(return_expressions) == 1:
            clauses.append(f"returns `{return_expressions[0]}`")
        else:
            clauses.append(f"has {len(return_expressions)} explicit return paths")
    if not clauses:
        clauses.append(
            "contains no state mutation, call, raise, return, await, or yield"
        )
    implementation = f"{kind.title()} `{qualname}` " + "; ".join(clauses) + "."
    return {
        "implementation": implementation,
        "decorators": decorators,
        "calls": calls,
        "state_reads": state_reads,
        "state_writes": state_writes,
        "raises": raises,
        "return_expressions": return_expressions,
        "awaits": awaits,
        "yields": yields,
    }


def _function_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Render a stable function signature without importing its module."""

    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    return f"{prefix} {node.name}({ast.unparse(node.args)}){returns}"


def _class_signature(node: ast.ClassDef) -> str:
    """Render a class declaration and its bases from the AST."""

    arguments = [ast.unparse(base) for base in node.bases]
    arguments.extend(ast.unparse(keyword) for keyword in node.keywords)
    suffix = f"({', '.join(arguments)})" if arguments else ""
    return f"class {node.name}{suffix}"


def _defined_member_names(tree: ast.Module) -> tuple[str, ...]:
    """Return names defined directly by a module in source order."""

    names: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.append(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets: Iterable[ast.expr]
            if isinstance(node, ast.Assign):
                targets = node.targets
            else:
                targets = (node.target,)
            for target in targets:
                if isinstance(target, ast.Name):
                    names.append(target.id)
    return tuple(dict.fromkeys(names))


def scan_python_file(path: Path, root: Path = REPOSITORY_ROOT) -> Module:
    """Parse one Python file into module and symbol documentation metadata."""

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent

    module_name = module_name_for_path(path, root)
    symbols: list[Symbol] = []
    definition_types = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)

    for node in ast.walk(tree):
        if not isinstance(node, definition_types):
            continue

        ancestors: list[ast.AST] = []
        current = parents.get(node)
        while current is not None:
            if isinstance(current, definition_types):
                ancestors.append(current)
            current = parents.get(current)
        ancestors.reverse()

        parent_definition = ancestors[-1] if ancestors else None
        has_function_ancestor = any(
            isinstance(ancestor, (ast.FunctionDef, ast.AsyncFunctionDef))
            for ancestor in ancestors
        )
        addressable = not has_function_ancestor
        qualified_parts = [ancestor.name for ancestor in ancestors] + [node.name]
        qualname = ".".join(qualified_parts)
        public = addressable and all(
            not part.startswith("_") for part in qualified_parts
        )

        docstring = ast.get_docstring(node, clean=True) or ""
        if isinstance(node, ast.ClassDef):
            kind = "nested class" if has_function_ancestor else "class"
            signature = _class_signature(node)
            parameters = _class_parameters(node, docstring)
            return_annotation = node.name
        elif has_function_ancestor:
            kind = "nested function"
            signature = _function_signature(node)
            parameters = _function_parameters(node, docstring)
            return_annotation = (
                _short_expression(node.returns)
                if node.returns is not None
                else "not annotated"
            )
        elif isinstance(parent_definition, ast.ClassDef):
            kind = "method"
            signature = _function_signature(node)
            parameters = _function_parameters(node, docstring)
            return_annotation = (
                _short_expression(node.returns)
                if node.returns is not None
                else "not annotated"
            )
        else:
            kind = "function"
            signature = _function_signature(node)
            parameters = _function_parameters(node, docstring)
            return_annotation = (
                _short_expression(node.returns)
                if node.returns is not None
                else "not annotated"
            )

        end_line = getattr(node, "end_lineno", None) or node.lineno
        source_url = (
            f"{REPOSITORY_URL}/blob/{SOURCE_BRANCH}/"
            f"{path.relative_to(root).as_posix()}#L{node.lineno}-L{end_line}"
        )
        facts = _implementation_facts(node, kind=kind, qualname=qualname)
        implementation = str(facts["implementation"])
        symbols.append(
            Symbol(
                name=node.name,
                qualname=qualname,
                full_name=f"{module_name}.{qualname}",
                kind=kind,
                signature=signature,
                parameters=parameters,
                return_annotation=return_annotation,
                docstring=docstring,
                summary=_first_sentence(docstring) or implementation,
                implementation=implementation,
                documented=bool(docstring),
                public=public,
                addressable=addressable,
                line=node.lineno,
                end_line=end_line,
                source_url=source_url,
                decorators=facts["decorators"],
                calls=facts["calls"],
                state_reads=facts["state_reads"],
                state_writes=facts["state_writes"],
                raises=facts["raises"],
                return_expressions=facts["return_expressions"],
                awaits=bool(facts["awaits"]),
                yields=bool(facts["yields"]),
            )
        )

    symbols.sort(key=lambda symbol: (symbol.line, symbol.end_line, symbol.qualname))
    module_docstring = ast.get_docstring(tree, clean=True) or ""
    relative_path = path.relative_to(root).as_posix()
    line_count = len(source.splitlines())
    return Module(
        name=module_name,
        path=relative_path,
        page_path=page_path_for_module(path, root).as_posix(),
        docstring=module_docstring,
        summary=_first_sentence(module_docstring) or f"Python module `{module_name}`.",
        line_count=line_count,
        source_url=(
            f"{REPOSITORY_URL}/blob/{SOURCE_BRANCH}/{relative_path}"
            f"#L1-L{max(line_count, 1)}"
        ),
        members=_defined_member_names(tree),
        symbols=tuple(symbols),
    )


def build_inventory(
    root: Path = REPOSITORY_ROOT,
    source_roots: tuple[str, ...] = ("vllm_mlx",),
) -> list[Module]:
    """Build static source inventory for the selected repository roots."""

    return [
        scan_python_file(path, root)
        for path in _tracked_python_files(root, source_roots)
    ]


def build_repository_inventory(root: Path = REPOSITORY_ROOT) -> list[Module]:
    """Inventory runtime, documentation tools, and executable examples."""

    return build_inventory(root, ("vllm_mlx", "scripts", "examples"))


def _literal_or_source(node: ast.AST | None, default: str = "") -> str:
    """Render a simple literal cleanly and preserve expressions as source."""

    if node is None:
        return default
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError):
        return " ".join(ast.unparse(node).split())
    if isinstance(value, str):
        return " ".join(value.split())
    return repr(value)


def scan_cli_options(
    paths: Iterable[Path], root: Path = REPOSITORY_ROOT
) -> list[CLIOption]:
    """Extract every argparse ``add_argument`` call from selected source files."""

    options: list[CLIOption] = []
    for path in sorted(paths):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        parents: dict[ast.AST, ast.AST] = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                parents[child] = parent
        module_name = module_name_for_path(path, root)
        relative_path = path.relative_to(root).as_posix()

        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_argument"
            ):
                continue
            flags = tuple(_literal_or_source(arg) for arg in node.args)
            if not flags:
                continue
            keywords = {keyword.arg: keyword.value for keyword in node.keywords}
            destination = _literal_or_source(keywords.get("dest"))
            if not destination:
                preferred = next(
                    (flag for flag in flags if flag.startswith("--")), flags[0]
                )
                destination = preferred.lstrip("-").replace("-", "_")

            ancestors: list[str] = []
            current = parents.get(node)
            while current is not None:
                if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    ancestors.append(current.name)
                current = parents.get(current)
            ancestors.reverse()
            context = ".".join([module_name, *ancestors])
            receiver = " ".join(ast.unparse(node.func.value).split())
            line = node.lineno
            end_line = getattr(node, "end_lineno", None) or line
            options.append(
                CLIOption(
                    context=context,
                    receiver=receiver,
                    flags=flags,
                    destination=destination,
                    description=_literal_or_source(keywords.get("help")),
                    default=_literal_or_source(
                        keywords.get("default"), "argparse default"
                    ),
                    required=(
                        _literal_or_source(keywords.get("required")) == "True"
                        or not flags[0].startswith("-")
                    ),
                    choices=_literal_or_source(keywords.get("choices")),
                    action=_literal_or_source(keywords.get("action")),
                    path=relative_path,
                    line=line,
                    end_line=end_line,
                    source_url=(
                        f"{REPOSITORY_URL}/blob/{SOURCE_BRANCH}/{relative_path}"
                        f"#L{line}-L{end_line}"
                    ),
                )
            )
    return sorted(options, key=lambda option: (option.path, option.line))


def build_cli_inventory(root: Path = REPOSITORY_ROOT) -> list[CLIOption]:
    """Build the complete argparse option inventory for executable source."""

    paths = _tracked_python_files(root, ("vllm_mlx", "scripts", "examples"))
    return scan_cli_options(paths, root)


def _escape_table_cell(value: str) -> str:
    """Escape text for a compact Markdown table cell."""

    return " ".join(value.replace("|", "\\|").split())


def render_callable_signature(symbol: Symbol, *, qualified: bool = False) -> str:
    """Render a reader-facing signature without implicit ``self`` or ``cls``."""

    pieces: list[str] = []
    positional_only_remaining = sum(
        parameter.kind == "positional-only" for parameter in symbol.parameters
    )
    has_variadic_positional = any(
        parameter.kind == "variadic positional" for parameter in symbol.parameters
    )
    keyword_separator_added = False
    for parameter in symbol.parameters:
        if parameter.kind == "keyword-only" and not (
            has_variadic_positional or keyword_separator_added
        ):
            pieces.append("*")
            keyword_separator_added = True
        piece = parameter.name
        if parameter.annotation != "not annotated":
            piece += f": {parameter.annotation}"
        if parameter.default:
            piece += f" = {parameter.default}"
        pieces.append(piece)
        if parameter.kind == "positional-only":
            positional_only_remaining -= 1
            if positional_only_remaining == 0:
                pieces.append("/")

    name = symbol.full_name if qualified else symbol.qualname
    async_prefix = "async " if symbol.signature.startswith("async def ") else ""
    signature = f"{async_prefix}{name}({', '.join(pieces)})"
    if symbol.kind not in {"class", "nested class"}:
        signature += f" -> {symbol.return_annotation}"
    return signature


def _symbol_details_url(module: Module, symbol: Symbol) -> str:
    """Return the generated details URL or source fallback for one symbol."""

    relative = Path(module.page_path).relative_to("reference")
    if relative.name == "index.md":
        page_url = relative.parent.as_posix() + "/"
    else:
        page_url = relative.with_suffix("").as_posix() + "/"
    return f"../{page_url}#contract-{symbol.full_name}"


def render_contract_details(module: Module) -> str:
    """Render explicit inputs and behavior for every definition in a module."""

    if not module.symbols:
        return "This module does not declare classes or functions.\n"
    lines: list[str] = []
    for symbol in module.symbols:
        lines.extend(
            [
                (
                    f'<details class="api-contract" id="contract-{symbol.full_name}" '
                    'markdown="1">'
                ),
                f"<summary><code>{symbol.full_name}</code> · {symbol.kind}</summary>",
                "",
                "```python",
                render_callable_signature(symbol, qualified=True),
                "```",
                "",
                symbol.summary,
                "",
                "**Parameters**",
                "",
            ]
        )
        if symbol.parameters:
            lines.extend(
                [
                    "| Name | Type | Required | Default | Description |",
                    "| --- | --- | --- | --- | --- |",
                ]
            )
            for parameter in symbol.parameters:
                lines.append(
                    "| "
                    f"`{parameter.name}` | `{_escape_table_cell(parameter.annotation)}` | "
                    f"`{'yes' if parameter.required else 'no'}` | "
                    f"`{_escape_table_cell(parameter.default or 'none')}` | "
                    f"{_escape_table_cell(parameter.description)} |"
                )
        else:
            lines.append("This callable has no explicit inputs.")
        lines.extend(
            [
                "",
                "**Returns**",
                "",
                (
                    f"- Type: `{symbol.return_annotation}`"
                    if symbol.kind not in {"class", "nested class"}
                    else f"- Constructs: `{symbol.full_name}`"
                ),
            ]
        )
        if symbol.return_expressions:
            lines.append(
                "- Direct return expressions: "
                + "; ".join(f"`{value}`" for value in symbol.return_expressions)
            )
        if symbol.yields:
            lines.append("- Yields values incrementally.")
        lines.extend(["", "**Exceptions and behavior**", "", symbol.implementation])
        if symbol.raises:
            lines.append(
                "Directly raised exceptions: "
                + ", ".join(f"`{name}`" for name in symbol.raises)
                + "."
            )
        else:
            lines.append("No direct `raise` statement appears in this definition.")
        lines.extend(
            [
                "",
                f"[View source #L{symbol.line}-L{symbol.end_line}]({symbol.source_url}).",
                "",
                "</details>",
                "",
            ]
        )
    return "\n".join(lines)


def render_source_map(module: Module) -> str:
    """Render a line-precise source table for every definition in a module."""

    if not module.symbols:
        return "This module does not declare classes or functions.\n"
    lines = [
        "| Symbol | Kind | Signature and inputs | What it does | Source |",
        "| --- | --- | --- | --- | --- |",
    ]
    for symbol in module.symbols:
        symbol_name = f"`{symbol.qualname}`"
        symbol_name = f"[`{symbol.qualname}`](#contract-{symbol.full_name})"
        lines.append(
            "| "
            f"{symbol_name} | {symbol.kind} | "
            f"`{_escape_table_cell(render_callable_signature(symbol))}` | "
            f"{_escape_table_cell(symbol.summary)} | "
            f"[#L{symbol.line}-L{symbol.end_line}]({symbol.source_url}) |"
        )
    return "\n".join(lines) + "\n"


def render_symbol_index(modules: list[Module]) -> str:
    """Render a filterable index of every runtime class and callable."""

    entries = sorted(
        ((module, symbol) for module in modules for symbol in module.symbols),
        key=lambda item: item[1].full_name.casefold(),
    )
    lines = [
        "# Python symbol index",
        "",
        "Search every runtime class, function, method, and nested helper by its exact Python name or input signature. Select a result to open its detailed API record. Source links are pinned to the immutable revision used to build this documentation.",
        "",
        '<div class="api-symbol-tools">',
        '  <label for="api-symbol-filter">Filter symbols</label>',
        '  <input id="api-symbol-filter" type="search" placeholder="Try SchedulerConfig, cache_ttl_seconds, or stream_outputs" autocomplete="off">',
        '  <label for="api-symbol-kind">Kind</label>',
        '  <select id="api-symbol-kind">',
        '    <option value="">All kinds</option>',
        '    <option value="class">Classes</option>',
        '    <option value="function">Functions</option>',
        '    <option value="method">Methods</option>',
        '    <option value="nested function">Nested functions</option>',
        "  </select>",
        f'  <p id="api-symbol-count" aria-live="polite">{len(entries)} symbols</p>',
        "</div>",
        "",
        '<div class="api-symbol-table" tabindex="0" aria-label="Python symbol index">',
        "<table>",
        "<thead><tr><th>Name</th><th>Kind</th><th>Signature and inputs</th><th>What it does</th><th>Source</th></tr></thead>",
        "<tbody>",
    ]
    for module, symbol in entries:
        signature = render_callable_signature(symbol, qualified=True)
        search_value = " ".join(
            (symbol.full_name, symbol.kind, signature, symbol.summary)
        ).casefold()
        details_url = _symbol_details_url(module, symbol)
        lines.extend(
            [
                (
                    f'<tr data-api-symbol data-symbol-kind="{html.escape(symbol.kind)}" '
                    f'data-symbol-search="{html.escape(search_value, quote=True)}">'
                ),
                f'<td><a href="{html.escape(details_url, quote=True)}"><code>{html.escape(symbol.full_name)}</code></a></td>',
                f"<td>{html.escape(symbol.kind)}</td>",
                f"<td><code>{html.escape(signature)}</code></td>",
                f"<td>{html.escape(symbol.summary)}</td>",
                (
                    f'<td><a href="{html.escape(symbol.source_url, quote=True)}">'
                    f"#L{symbol.line}-L{symbol.end_line}</a></td>"
                ),
                "</tr>",
            ]
        )
    lines.extend(["</tbody>", "</table>", "</div>", ""])
    return "\n".join(lines)


def render_module_page(module: Module) -> str:
    """Render the generated MkDocs page for one Python module."""

    lines = [
        f"# `{module.name}`",
        "",
        module.summary,
        "",
        (
            f"[View the complete module source at #L1-L{module.line_count}]"
            f"({module.source_url})."
        ),
        "",
        "## API details",
        "",
        "Each callable below includes its exact signature, type annotations, inputs, defaults, return contract, documented exceptions, implementation source, and parsed docstring sections when the source provides them.",
        "",
        f"::: {module.name}",
        "    options:",
        "      members:",
    ]
    if module.members:
        lines.extend(f"        - {member}" for member in module.members)
    else:
        lines.append("        []")
    lines.extend(
        [
            "      filters: []",
            "      show_if_no_docstring: true",
            "",
            "## Complete contract reference",
            "",
            "Expand any definition for its exact inputs, annotations, defaults, return contract, directly raised exceptions, source-grounded behavior, and immutable line link. This section includes private and nested definitions that ordinary API generators omit.",
            "",
            render_contract_details(module).rstrip(),
            "",
            "## Complete symbol map",
            "",
            "This map also includes private definitions and nested helpers. The signature column exposes every explicit input even when an internal helper has no dedicated parameter prose.",
            "",
            render_source_map(module).rstrip(),
            "",
        ]
    )
    return "\n".join(lines)


def render_module_for_llms(module: Module) -> str:
    """Render a self-contained plain-Markdown API record for language models."""

    lines = [
        f"# Module `{module.name}`",
        "",
        module.docstring or module.summary,
        "",
        f"Source: {module.source_url}",
    ]
    for symbol in module.symbols:
        lines.extend(
            [
                "",
                f"## `{symbol.full_name}`",
                "",
                f"- Kind: {symbol.kind}",
                f"- Signature: `{symbol.signature}`",
                f"- Source: {symbol.source_url}",
                f"- Implementation: {symbol.implementation}",
                "",
                symbol.docstring or symbol.summary,
            ]
        )
        if symbol.parameters:
            lines.append("- Inputs:")
            for parameter in symbol.parameters:
                requirement = "required" if parameter.required else "optional"
                default = (
                    f"; default `{parameter.default}`" if parameter.default else ""
                )
                lines.append(
                    f"  - `{parameter.name}` ({parameter.annotation}; {requirement}"
                    f"{default}): {parameter.description}"
                )
        else:
            lines.append("- Inputs: none")
        if symbol.kind in {"class", "nested class"}:
            lines.append(f"- Constructs: `{symbol.full_name}`")
        else:
            lines.append(f"- Return annotation: `{symbol.return_annotation}`")
        if symbol.decorators:
            lines.append(f"- Decorators: {', '.join(symbol.decorators)}")
        if symbol.calls:
            lines.append(f"- Calls: {', '.join(symbol.calls)}")
        if symbol.state_reads:
            lines.append(f"- State reads: {', '.join(symbol.state_reads)}")
        if symbol.state_writes:
            lines.append(f"- State writes: {', '.join(symbol.state_writes)}")
        if symbol.raises:
            lines.append(f"- Raises directly: {', '.join(symbol.raises)}")
        if symbol.return_expressions:
            lines.append(
                f"- Return expressions: {'; '.join(symbol.return_expressions)}"
            )
    return "\n".join(lines) + "\n"


def render_cli_reference(options: list[CLIOption]) -> str:
    """Render every discovered argparse option as a line-precise reference."""

    lines = [
        "# Complete CLI option inventory",
        "",
        "This page is generated from every `add_argument` declaration in the runtime, maintenance scripts, and runnable examples. The hand-written [CLI guide](cli.md) explains supported workflows.",
        "",
    ]
    current_context = ""
    current_receiver = ""
    for option in options:
        if option.context != current_context:
            current_context = option.context
            current_receiver = ""
            lines.extend([f"## `{current_context}`", ""])
        if option.receiver != current_receiver:
            current_receiver = option.receiver
            lines.extend([f"### Parser `{current_receiver}`", ""])
        flags = ", ".join(f"`{flag}`" for flag in option.flags)
        lines.extend(
            [
                f"#### {flags}",
                "",
                option.description or "No argparse help text is declared.",
                "",
                f"- Destination: `{option.destination}`",
                f"- Required: `{str(option.required).lower()}`",
                f"- Default: `{option.default}`",
                f"- Choices: `{option.choices or 'not restricted'}`",
                f"- Action: `{option.action or 'store'}`",
                f"- Source: [L{option.line}-L{option.end_line}]({option.source_url})",
                "",
            ]
        )
    return "\n".join(lines)
