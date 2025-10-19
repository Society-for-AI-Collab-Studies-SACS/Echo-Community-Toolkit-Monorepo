load("@rules_python//python:defs.bzl", "py_binary")
load("@pip_deps//:requirements.bzl", "requirement")

py_binary(
    name = "mock_services",
    srcs = ["mock_services.py"],
    python_version = "PY3",
    deps = [
        "//protos:agents_py_proto",
        "//protos:agents_py_grpc",
        requirement("grpcio"),
        requirement("protobuf"),
    ],
)

py_binary(
    name = "test_client",
    srcs = ["test_client.py"],
    python_version = "PY3",
    deps = [
        "//protos:agents_py_proto",
        "//protos:agents_py_grpc",
        requirement("grpcio"),
        requirement("protobuf"),
    ],
)
