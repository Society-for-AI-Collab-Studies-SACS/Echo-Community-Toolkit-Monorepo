load("@rules_proto//proto:defs.bzl", "proto_library")
load("@rules_proto_grpc//python:defs.bzl", "py_proto_library", "py_grpc_library")

proto_library(
    name = "agents_proto",
    srcs = ["agents.proto"],
    deps = ["@com_google_protobuf//:empty_proto"],
)

py_proto_library(
    name = "agents_py_proto",
    deps = [":agents_proto"],
)

py_grpc_library(
    name = "agents_py_grpc",
    deps = [":agents_proto"],
)

