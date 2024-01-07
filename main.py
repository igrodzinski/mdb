import sys

from flask import Flask, render_template

#run app
#python -m flask --app main --debug run

app = Flask(__name__)
CERTS = None
AUDIENCE = None


# [START getting_started_auth_certs]
def certs():
    """Returns a dictionary of current Google public key certificates for
    validating Google-signed JWTs. Since these change rarely, the result
    is cached on first request for faster subsequent responses.
    """
    import requests

    global CERTS
    if CERTS is None:
        response = requests.get(
            'https://www.gstatic.com/iap/verify/public_key'
        )
        CERTS = response.json()
    return CERTS
# [END getting_started_auth_certs]


# [START getting_started_auth_metadata]
def get_metadata(item_name):
    """Returns a string with the project metadata value for the item_name.
    See https://cloud.google.com/compute/docs/storing-retrieving-metadata for
    possible item_name values.
    """
    import requests

    endpoint = 'http://metadata.google.internal'
    path = '/computeMetadata/v1/project/'
    path += item_name
    response = requests.get(
        '{}{}'.format(endpoint, path),
        headers={'Metadata-Flavor': 'Google'}
    )
    metadata = response.text
    return metadata
# [END getting_started_auth_metadata]


# [START getting_started_auth_audience]
def audience():
    """Returns the audience value (the JWT 'aud' property) for the current
    running instance. Since this involves a metadata lookup, the result is
    cached when first requested for faster future responses.
    """
    global AUDIENCE
    if AUDIENCE is None:
        project_number = get_metadata('numeric-project-id')
        project_id = get_metadata('project-id')
        AUDIENCE = '/projects/{}/apps/{}'.format(
            project_number, project_id
        )
    return AUDIENCE
# [END getting_started_auth_audience]


# [START getting_started_auth_validate_assertion]
def validate_assertion(assertion):
    """Checks that the JWT assertion is valid (properly signed, for the
    correct audience) and if so, returns strings for the requesting user's
    email and a persistent user ID. If not valid, returns None for each field.
    """
    from jose import jwt

    try:
        info = jwt.decode(
            assertion,
            certs(),
            algorithms=['ES256'],
            audience=audience()
            )
        return info['email'], info['sub']
    except Exception as e:
        print('Failed to validate assertion: {}'.format(e), file=sys.stderr)
        return None, None
# [END getting_started_auth_validate_assertion]

@app.route("/")
def hello_world():
    return render_template('index.html')
@app.route("/info")
def info():
    to_do_list =["1. logowanie","1.1 pobrać dane z gcp"]
    return render_template('info.html', list = to_do_list)
@app.route('/login', methods=['GET'])
def say_hello():
    from flask import request

    assertion = request.headers.get('X-Goog-IAP-JWT-Assertion')
    email, id = validate_assertion(assertion)
    page = "<h1>Hello {}</h1>".format(email)
    return render_template('logged.html', email = email)

if __name__ == "__main__":
    # only for development
    app.run(debug=True)