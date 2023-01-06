#!python
import os
import subprocess
import base64
from pathlib import Path
import yaml


def run_cmd(cmd):
    print("Running cmd: " + cmd)
    output = os.popen(cmd).read()
    print(output)
    return output


BASE_DIR = str(Path(__file__).resolve().parent)

output = os.popen('git pull').read()
print(output)

ver_num = subprocess.check_output(["git", "describe", "--tags", "--always"], cwd=BASE_DIR).decode('utf-8').strip()

yaml_values = yaml.load(open('helm-chart/values.yaml', 'r').read(), yaml.CLoader)
image_name = yaml_values["image_name"]
namespace = yaml_values["namespace"]

# Run the certgen.sh script to create the self-signed SAN certificates for the admission controller.
run_cmd('./certgen.sh')

# Get the base64 value of the ca.crt file created by the certgen.sh script.
ca_key = open('certs/wardenkey.pem', 'rb').read()
ca_bundle = base64.b64encode(ca_key).decode()
# ca_bundle = run_cmd("cat certs/ca.crt | base64")
# Paste the base64 value into the caBundle location in the webhook.yaml file.
yaml_values["ver_num"] = ver_num
yaml_values["ca_bundle"] = ca_bundle
yaml.dump(yaml_values, open('helm-chart/values.yaml', 'w'), yaml.CDumper)
# Build the container using the Dockerfile within the directory. Push the image to your image repository
run_cmd('docker build -t %s:%s .' % (image_name, ver_num))
run_cmd('docker push %s:%s' % (image_name, ver_num))
# Update the warden-k8s.yaml file to point to your new image.
# This is handled by the HELM Chart
warden_yaml = run_cmd("helm template warden helm-chart/ -n %s " % namespace)
f = open('deployment_yaml/warden.yaml', 'w')
f.write(warden_yaml)
f.close()
# Delete any existing objects
run_cmd("kubectl delete -f deployment_yaml/warden.yaml")
# Apply the warden-k8s.yaml file to deploy your admission controller within the cluster.
# Apply the webhook.yaml file to deploy the validation configuration to the Kubernetes API server.
run_cmd("kubectl apply -f deployment_yaml/warden.yaml")
