import ics
import re
import requests
from flask import Flask, make_response, request, send_from_directory


# TODO: estä rekursiiviset requestit takas tälle sivulle
# TODO: Estä julmetun kokoisten tiedostojen lataus


def regexStringMaker(course=None, toKeep=None, toRemovePrefix=None):
    if course is None: course = ""
    if toKeep is None: toKeep = ""
    if toRemovePrefix is None: toRemovePrefix = ""
    return fr"^(?!{'|'.join(toKeep.split(','))})({'|'.join(toRemovePrefix)})(\d\d).*{course}"


def multiRegexStringMaker(course=None, toKeep=None, toRemovePrefix=None):
    if course is None: course = []
    if toKeep is None: toKeep = []
    if toRemovePrefix is None: toRemovePrefix = []
    parts = []
    if len(course) != len(toKeep) or len(toKeep) != len(toRemovePrefix):
        exit(1)  # Ei saa tulla erimittaisia taulukoita
    for i in range(len(course)):
        parts.append(regexStringMaker(course=course[i],
                                      toKeep=toKeep[i],
                                      toRemovePrefix=toRemovePrefix[i]))
    return fr"({'|'.join(parts)})"


def makeRegex(param):
    if "~" in param:
        parts = [newRegexMaker(part) for part in param.split("~")]
        return fr"({'|'.join(parts)})"
    else:
        return newRegexMaker(param)


def newRegexMaker(s):
    parts = s.split(",")
    course = parts[0]
    tail = parts[1:]
    excludes = [e for e in tail if len(e) == 3]
    prefix = set([w[0] for w in tail if len(w) > 0])
    removables = [fr"{p}\d\d" for p in prefix]
    exstring = fr"(?!{'|'.join(excludes)})" if len(excludes) > 0 else ""
    return fr"{exstring}({'|'.join(removables)}).*{course}"


def filterEvents(cal, regex):
    toRemove = []
    for e in cal.events:
        if regex.search(e.name):
            toRemove.append(e)

    for e in toRemove:
        cal.events.remove(e)


app = Flask(__name__)


@app.route("/calendar/")
def getFilteredCal():
    o_url = request.args.get("url")
    print("Original url:")
    print(o_url)
    courses = request.args.get("courses")
    includes = request.args.get("includes")
    ex_prefix = request.args.get("excludeprefix")
    regex = re.compile(regexStringMaker(course=courses, toKeep=includes, toRemovePrefix=ex_prefix))

    calendar = ics.Calendar(requests.get(o_url).text)
    filterEvents(calendar, regex)
    response = make_response(str(calendar))
    response.headers["Content-Disposition"] = "attachment; filename=calendar.ics"
    return response


@app.route("/calendar/myco/")
def myCoCalendar():
    uid = request.args.get("userid")
    token = request.args.get("authtoken")
    o_url = f"https://mycourses.aalto.fi/calendar/export_execute.php?userid={uid}&authtoken={token}&preset_what=all&preset_time=recentupcoming"
    courses = request.args.get("courses")
    includes = request.args.get("includes")
    ex_prefix = request.args.get("excludeprefix")
    regex = re.compile(regexStringMaker(course=courses, toKeep=includes, toRemovePrefix=ex_prefix))

    calendar = ics.Calendar(requests.get(o_url).text)
    filterEvents(calendar, regex)
    response = make_response(str(calendar))
    response.headers["Content-Disposition"] = "attachment; filename=calendar.ics"
    return response


@app.route("/calendar/myco2/")
def myCoCalendar2():
    try:
        uid = request.args.get("userid")
        token = request.args.get("authtoken")
        param = request.args.get("f")
    except:
        return "Bad parameters"
    o_url = f"https://mycourses.aalto.fi/calendar/export_execute.php?userid={uid}&authtoken={token}&preset_what=all&preset_time=recentupcoming"
    regex = re.compile(makeRegex(param))
    calendar = ics.Calendar(requests.get(o_url).text)
    filterEvents(calendar, regex)
    response = make_response(str(calendar))
    response.headers["Content-Disposition"] = "attachment; filename=calendar.ics"
    return response


@app.route("/test/")
def testIsServerRunning():
    f = request.args.get("f")
    return f"Server running, n_f={len(f)}\nregex from f={makeRegex(f)}"


@app.route('/<file>')
def home(file):
    return send_from_directory("static", file)
