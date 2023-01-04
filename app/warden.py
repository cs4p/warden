from flask import Flask, request, jsonify
import base64
import jsonpatch

warden = Flask(__name__)


# POST route for Admission Controller
@warden.route('/validate', methods=['POST'])
# Admission Control Logic
def deployment_webhook():
    request_info = request.get_json()
    uid = request_info["request"].get("uid")
    try:
        if request_info["request"]["object"]["metadata"]["labels"].get("omb"):
            # Send response back to controller if validations succeeds
            return k8s_response(True, uid, "omb label exists")
    except:
        return k8s_response(False, uid, "No labels exist. An omb label is required")

    # Send response back to controller if failed
    return k8s_response(False, uid, "Not allowed without an omb label")

# Function to respond back to the Admission Controller
def k8s_response(allowed, uid, message):
    return jsonify({"apiVersion": "admission.k8s.io/v1", "kind": "AdmissionReview",
                    "response": {"allowed": allowed, "uid": uid, "status": {"message": message}}})

@warden.route('/mutate', methods=['POST'])
def mutating_webhook():
    request_info = request.get_json()
    uid = request_info["request"].get("uid")
    return k8s_response_patch(True, uid, "Adding omb label", json_patch=jsonpatch.JsonPatch(
        [{"op": "add", "path": "/metadata/labels/omb", "value": "yes"}]))

def k8s_response_patch(allowed, uid, message, json_patch):
    base64_patch = base64.b64encode(json_patch.to_string().encode("utf-8")).decode("utf-8")
    return jsonify({"response": {"allowed": allowed,
                                 "uid": uid,
                                 "status": {"message": message},
                                 "patchType": "JSONPatch",
                                 "patch": base64_patch}})
if __name__ == '__main__':
    warden.run(ssl_context=('../certs/wardencrt.pem', '../certs/wardenkey.pem'), debug=True, host='0.0.0.0', port=5001)
