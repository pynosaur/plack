genrule(
    name = "plack_bin",
    srcs = glob(["app/**/*.py", "doc/**/*.yaml"]),
    outs = ["plack"],
    cmd = """
        /opt/homebrew/bin/nuitka \
            --onefile \
            --include-data-dir=doc=doc \
            --onefile-tempdir-spec=/tmp/nuitka-plack \
            --no-progressbar \
            --assume-yes-for-downloads \
            --no-deployment-flag=self-execution \
            --output-dir=$$(dirname $(location plack)) \
            --output-filename=plack \
            $(location app/main.py)
    """,
    local = 1,
    visibility = ["//visibility:public"],
)
