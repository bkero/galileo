# Booger D 2
# REST API in front of snot
import subprocess
import pysnot

import uuid
import yaml


from flask import Flask, abort, request, jsonify
from flask_cors import CORS
from itsdangerous import TimestampSigner


app = Flask(__name__)
app.config['CORS_HEADERS'] = 'X-SNOT-Auth-Key'
cors = CORS(app)

def verify_auth():
    if conf['verify_auth']:
        try:
            s.unsign(request.headers['X-SNOT-Auth-Key'], max_age=1500)
        except:
            abort(401)


@app.route("/")
def hello():
    return "Boogerd 2"


@app.route("/v1/ticket/<int:ticket_number>")
def ticket_get(ticket_number):
    verify_auth()

    tic = pysnot.get_ticket(ticket_number)
    resp = {"ticket_number": ticket_number,
            "content": tic}
    return jsonify(resp)


@app.route("/v1/ticket/<int:ticket_number>/raw")
def ticket_get_raw(ticket_number):
    verify_auth()

    tic = pysnot.get_ticket_raw(ticket_number)
    resp = {"ticket_number": ticket_number,
            "content": tic}
    return jsonify(resp)


@app.route("/v1/ticket/<int:ticket_number>/flags")
def ticket_flags_get(ticket_number):
    verify_auth()

    flags = pysnot.get_flags(ticket_number)
    resp = {"ticket_number": ticket_number,
            "flags": flags}
    return jsonify(resp)


@app.route("/v1/ticket/<int:ticket_number>/reply_to")
def ticket_reply_to_get(ticket_number):
    verify_auth()

    reply_to_string = pysnot.get_reply_to(ticket_number)
    return reply_to_string


@app.route("/v1/ticket/<int:ticket_number>/subject")
def ticket_subject_get(ticket_number):
    verify_auth()

    subject = pysnot.get_subject(ticket_number)
    return subject


@app.route("/v1/ticket/<int:ticket_number>/assigned")
def ticket_assigned_get(ticket_number):
    verify_auth()
    #TODO add a handler for accept: application/json

    assigned = pysnot.get_assigned(ticket_number)
    if assigned is None:
        resp = {"ticket_number": ticket_number,
                "assigned": False}
        return jsonify(resp)
    resp = {"ticket_number": ticket_number,
            "assigned": assigned}
    return jsonify(resp)


@app.route("/v1/ticket/<int:ticket_number>/metadata")
def ticket_metadata_get(ticket_number):
    verify_auth()

    metadata = pysnot.get_metadata(ticket_number)
    return jsonify(metadata)


@app.route("/v1/ticket/<int:ticket_number>/resolve_silent", methods=['POST'])
def ticket_resolve(ticket_number):
    verify_auth()

    success = pysnot.resolve_ticket_silent(ticket_number)
    if success:
        resp = {"ticket_number": ticket_number,
                "assigned": False}
        return jsonify(resp)
    else:
        abort(400, "Failed for unknown reasons")


@app.route("/v1/ticket/<int:ticket_number>/unassign", methods=['POST'])
def ticket_unassign(ticket_number):
    verify_auth()

    success = pysnot.unassign_ticket(ticket_number)
    if success:
        resp = {"ticket_number": ticket_number,
                "assigned": False}
        return jsonify(resp)
    else:
        abort(400, "Failed for unknown reasons")


@app.route("/v1/ticket/<int:ticket_number>/assign", methods=['POST'])
def ticket_assign(ticket_number):
    verify_auth()
    data = request.get_json(force=True)
    username = data['user']
    if '@' not in username:
        abort(400, "You must specify an email address")

    success = pysnot.assign_ticket(ticket_number, data['user'])
    if success:
        resp = {"ticket_number": ticket_number,
                "assigned": username}
        return jsonify(resp)
    else:
        abort(400, "Failed for unknown reasons")


@app.route("/v1/ticket/<int:ticket_number>/close", methods=['POST'])
def ticket_close(ticket_number):
    verify_auth()
    assigned = pysnot.get_assigned(ticket_number)
    if assigned is None:
        assigned = 'nobody@cat.pdx.edu'

    msg = pysnot.resolve_ticket(ticket_number, assigned)

    #TODO: unpack this a bit
    return jsonify({"message": str(msg)})


@app.route("/v1/ticket/<int:ticket_number>/update", methods=['POST'])
def ticket_update(ticket_number):
    verify_auth()
    data = request.get_json(force=True)
    user = data.get('user')
    to = data.get('to')
    subject = data.get('subject')
    message = data.get('message')
    if '@' not in user:
        abort(400, "You must specify an email address")
    if message is None:
        abort(400, "You must specify a message")

    msg = pysnot.update_ticket(ticket_number,
                               to=to,
                               user=user,
                               subject=subject,
                               message=message)

    #TODO: unpack this a bit
    return jsonify({"message": str(msg)})


@app.route("/v1/ticket/create", methods=['POST'])
def ticket_create():
    verify_auth()
    ticket_uuid = uuid.uuid4()
    data = request.get_json(force=True)
    user = data.get('user')
    cc = data.get('cc')
    subject = data.get('subject')
    message = data.get('message')
    if '@' not in user:
        abort(400, "You must specify an email address")
    if message is None:
        abort(400, "You must specify a message")
    if subject is None:
        abort(400, "You must specify a subject")

    headers = {'X-Boogerd-UUID': '{0}'.format(str(ticket_uuid))}

    msg = pysnot.create_ticket(user=user,
                               subject=subject,
                               message=message,
                               headers=headers)

    #TODO: unpack this a bit
    return jsonify({"uuid": str(ticket_uuid),
                    "extra_info": "ask snotrocket",
                    "message": str(msg)})




@app.route("/v1/all_flags")
def all_flags():
    verify_auth()

    flags = pysnot.list_all_flags()
    #this looks funky because of
    #http://flask.pocoo.org/docs/0.10/security/#json-security
    return jsonify({"all_flags": flags})


@app.errorhandler(400)
def custom400(error):
    verify_auth()
    response = jsonify({'message': error.description})
    response.status_code = 404
    response.status = 'error.Bad Request'
    return response


if __name__ == "__main__":
    with open('config.yaml') as f:
        conf = yaml.load(f.read())
    f.closed
    s = TimestampSigner(conf['secret_key'])

    app.run(debug=conf['debug'], port=conf['port'])
