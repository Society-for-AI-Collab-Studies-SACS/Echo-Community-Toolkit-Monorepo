load("@rules_python//python:defs.bzl", "py_binary")
load("@pip_deps//:requirements.bzl", "requirement")

py_binary(
    name = "kira_agent",
    srcs = ["kira_agent.py"],
    python_version = "PY3",
    deps = [
        requirement("aiohttp"),
    ],
)

