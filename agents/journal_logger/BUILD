load("@rules_python//python:defs.bzl", "py_binary")
load("@pip_deps//:requirements.bzl", "requirement")

py_binary(
    name = "journal_logger",
    srcs = ["journal_logger.py"],
    python_version = "PY3",
    deps = [
        "//protos:agents_py_proto",
        "//protos:agents_py_grpc",
        requirement("grpcio"),
        requirement("protobuf"),
        # Optional voice dependencies
        requirement("SpeechRecognition"),
        # PyAudio is optional and may need system support; not required here
    ],
)

