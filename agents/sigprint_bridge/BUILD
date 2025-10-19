load("@rules_python//python:defs.bzl", "py_binary")
load("@pip_deps//:requirements.bzl", "requirement")

py_binary(
    name = "sigprint_bridge",
    srcs = ["sigprint_bridge.py"],
    python_version = "PY3",
    deps = [
        "//protos:agents_py_proto",
        "//protos:agents_py_grpc",
        requirement("grpcio"),
        requirement("protobuf"),
        requirement("websockets"),
        requirement("pyserial"),
    ],
)

