import ics
import re
import requests
from flask import Flask, make_response, request, send_from_directory


# TODO: estä rekursiiviset requestit takas tälle sivulle
# TODO: Estä julmetun kokoisten tiedostojen lataus

app = Flask(__name__)


def make_regex(param):
    if "~" in param:
        parts = [make_regex_part(part) for part in param.split("~")]
        return fr"({'|'.join(parts)})"
    else:
        return make_regex_part(param)


def make_regex_part(s):
    parts = s.split(",")
    course = parts[0]
    tail = parts[1:]
    excludes = [e for e in tail if len(e) == 3]  # Pitää asian vain jos se on tasan kolme merkkiä pitkä
    prefix = set([w[0] for w in tail if len(w) > 0])
    removables = [fr"{p}\d\d" for p in prefix]
    exstring = fr"(?!{'|'.join(excludes)})" if len(excludes) > 0 else ""
    return fr"{exstring}({'|'.join(removables)}).*{course}"


def filter_events(cal, regex):
    to_remove = []
    for e in cal.events:
        if regex.search(e.name):
            to_remove.append(e)

    for e in to_remove:
        cal.events.remove(e)


@app.route("/calendar/")
def myco_calendar():
    try:
        uid = request.args.get("userid")
        token = request.args.get("authtoken")
        param = request.args.get("f")
    except:
        return "Bad parameters"
    o_url = f"https://mycourses.aalto.fi/calendar/export_execute.php?userid={uid}&authtoken={token}&preset_what=all&preset_time=recentupcoming"
    regex = re.compile(make_regex(param))
    calendar = ics.Calendar(requests.get(o_url).text)
    filter_events(calendar, regex)
    response = make_response(str(calendar))
    response.headers["Content-Disposition"] = "attachment; filename=calendar.ics"
    return response


@app.route('/<file>')
def home(file):
    return send_from_directory("static", file)
