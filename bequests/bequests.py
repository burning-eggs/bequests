import os
import sys
import json
import argparse
import requests

from collections import namedtuple
from requests.structures import CaseInsensitiveDict
from pretty import prettify


__author__ = "wake-code"
__version__ = "0.0.1a"


DEFAULT_UA = "bequests v%s" % __version__
SEP_COMMON = ":"
SEP_DATA = "="
TYPE_FORM = "application/x-www-form-urlencoded; charset=utf-8"
TYPE_JSON = "application/json; charset=utf-8"


KeyValue = namedtuple("KeyValue", ["key", "value", "sep"])


class KeyValueType(object):
    def __init__(self, separators):
        self.separators = separators

    def __call__(self, string: str):
        found = {
            string.find(sep): sep for sep in self.separators if string.find(sep) != -1
        }

        if not found:
            raise argparse.ArgumentTypeError("'%s' is not a valid value" % string)

        sep = found[min(found.keys())]
        key, value = string.split(sep, 1)

        return KeyValue(key=key, value=value, sep=sep)


parser = argparse.ArgumentParser(description="bequests - CLI HTTPS Client")

group = parser.add_mutually_exclusive_group(required=False)  # Content Type
group.add_argument(
    "--json",
    "-j",
    action="store_true",
    help="Serialize data items as a JSON Object and set 'Content-Type' to 'application/json' if not specified.",
)

group.add_argument(
    "--form",
    "-f",
    action="store_true",
    help="Serialize data items as Form Values and set 'Content-Type' to 'application/x-www-form-urlencoded' if not specified.",
)

parser.add_argument(
    "--ugly",
    "-u",
    help="Don't prettify the response.",
    dest="prettify",
    action="store_false",
    default=True,
)

parser.add_argument("--auth", help="username : password", type=KeyValueType(SEP_COMMON))

parser.add_argument(
    "--verify",
    help="Set to 'yes' to check the hosts SSL Certification. You can also pass a path to the CA_BUNDLE file for private certificates. You can also set the REQUESTS_CA_BUNDLE environment variable.",
)

parser.add_argument(
    "--proxy",
    default=[],
    action="append",
    type=KeyValueType(SEP_COMMON),
    help="String mapping protocol to the URL of the proxy (e.g. http:foo.bar:3128).",
)

parser.add_argument(
    "--allow-redirects",
    default=False,
    action="store_true",
    help="Set this flag if full redirects are allowed.",
)

parser.add_argument(
    "--file",
    metavar="PATH",
    type=argparse.FileType(),
    default=[],
    action="append",
    help="File to multipart load.",
)

parser.add_argument(
    "--timeout", type=float, help="Describes the timeout of the request."
)

parser.add_argument("method", help="HTTP Method to be used for the request.")

parser.add_argument(
    "url",
    metavar="URL",
    help="Protocol defaults to 'http://' if the url doesn't include it.",
)

parser.add_argument(
    "items",
    metavar="item",
    nargs="*",
    type=KeyValueType([SEP_COMMON, SEP_DATA]),
    help="HTTP Header (key : value) or data field (key = value).",
)


def main():
    args = parser.parse_args()
    headers = CaseInsensitiveDict()
    headers["User-Agent"] = DEFAULT_UA
    data = {}

    for item in args.items:
        if item.sep == SEP_COMMON:
            target = headers
        else:
            if not sys.stdin.isatty():
                parser.error(
                    "Request Body (stdin) and Request Data (key = value) cannot be mixed."
                )

            target = data

        target[item.key] = item.value

    if not sys.stdin.isatty():
        data = sys.stdin.read()

    if args.json or (not args.form and data):
        if sys.stdin.isatty():
            data = json.dumps(data)
        if "Content-Type" not in headers and (data or args.json):
            headers["Content-Type"] = TYPE_JSON
    elif "Content-Type" not in headers:
        headers["Content-Type"] = TYPE_FORM

    response = requests.request(
        method=args.method.lower(),
        url=args.url if "://" in args.url else "http://%s" % args.url,
        headers=headers,
        data=data,
        verify=True if args.verify == "yes" else args.verify,
        timeout=args.timeout,
        auth=(args.auth.key, args.auth.value) if args.auth else None,
        proxies={proxy.key: proxy.value for proxy in args.proxy},
        files={os.path.basename(f.name): f for f in args.file},
    )

    original = response.raw._original_response  # noqa
    response_bits = (
        u"HTTP/{version} {status} {reason}".format(
            version=".".join(str(original.version)),
            status=original.status,
            reason=original.reason,
        ),
        str(original.msg).decode("utf-8"),
        response.content.decode("utf-8") if response.content else u"",
    )

    if args.prettify and sys.stdout.isatty():
        response_bits = prettify(response.headers["content-type"], *response_bits)

    print(u"\n".join(response_bits))


if __name__ == "__main__":
    main()
