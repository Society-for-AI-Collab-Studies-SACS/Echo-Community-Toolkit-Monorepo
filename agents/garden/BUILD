load("@rules_python//python:defs.bzl", "py_binary")
load("@pip_deps//:requirements.bzl", "requirement")

py_binary(
    name = "narrative_agent",
    srcs = ["narrative_agent.py"],
    python_version = "PY3",
    deps = [
        "//protos:agents_py_proto",
        "//protos:agents_py_grpc",
        requirement("numpy"),
        requirement("grpcio"),
        requirement("protobuf"),
    ],
)
