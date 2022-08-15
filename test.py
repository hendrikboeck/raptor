from http import HTTPStatus

import raptor
from flask import Response, jsonify, make_response


def hello_world() -> Response:
    return make_response(jsonify(msg="Hello World"), HTTPStatus.OK.value)


def test(a: str) -> Response:
    return make_response(jsonify(a=a), HTTPStatus.OK.value)


def main() -> None:
    raptor.tools.io.configure("debug")

    rt = raptor.Router(propagate_errors=False)
    rt.mount("/hello_world", hello_world, ["GET"])
    rt.mount("/test/{a:hex}", test, ["GET"])

    pv = rt.build_provider("flask")
    pv.serve("127.0.0.1", 4321)


if __name__ == "__main__":
    main()
