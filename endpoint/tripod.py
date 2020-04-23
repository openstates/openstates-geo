import os
import glob
import subprocess
import zipfile
import boto3


def create_psycopg2_layer():
    if not os.path.exists("awslambda-psycopg2"):
        subprocess.run(
            ["git", "clone", "git@github.com:jkehler/awslambda-psycopg2.git"],
            check=True,
        )
    prefix = "awslambda-psycopg2/psycopg2-3.7/"
    with zipfile.ZipFile("psycopg2.zip", "w") as lz:
        for file in glob.glob(prefix + "*"):
            arcname = file.replace(prefix, "python/psycopg2/")
            lz.write(file, arcname)

    # upload
    client = boto3.client("lambda")
    client.publish_layer_version(
        LayerName="py37-psycopg2",
        Description="python 3.7 psycopg2 layer",
        Content={"ZipFile": open("psycopg2.zip", "rb").read()},
        CompatibleRuntimes=["python3.7"],
    )


def create_function(
    name,
    filename,
    *,
    role_arn,
    handler,
    runtime="python3.7",
    description="",
    environment=None,
):
    zipfilename = "upload.zip"
    with zipfile.ZipFile(zipfilename, "w") as zf:
        zf.write(filename)

    client = boto3.client("lambda")

    versions = client.list_layer_versions(LayerName="py37-psycopg2")
    # TODO: is zero the right index?
    layer_arn = versions["LayerVersions"][0]["LayerVersionArn"]

    try:
        existing_config = client.get_function_configuration(FunctionName=name)
    except client.exceptions.ResourceNotFoundException:
        existing_config = False
        client.create_function(
            FunctionName=name,
            Runtime=runtime,
            Role=role_arn,
            Handler=handler,
            Code={"ZipFile": open(zipfilename, "rb").read()},
            Description=description,
            Environment={"Variables": environment or {}},
            Publish=True,
            Layers=[layer_arn],
        )
        print("created function")

    if existing_config:
        client.update_function_code(
            FunctionName=name, ZipFile=open(zipfilename, "rb").read()
        )
        client.update_function_configuration(
            FunctionName=name,
            Role=role_arn,
            Handler=handler,
            Description=description,
            Environment={"Variables": environment or {}},
        )
        client.publish_version(FunctionName=name)
        print("updated function")


def main():
    create_function(
        "v3-district-geo",
        "lookup.py",
        role_arn="arn:aws:iam::189670762819:role/v3_lambda_exec_role",
        handler="lookup.lambda_handler",
        environment={
            "DB_HOST": os.environ["DB_HOST"],
            "DB_USER": os.environ["DB_USER"],
            "DB_NAME": os.environ["DB_NAME"],
            "DB_PASSWORD": os.environ["DB_PASSWORD"],
        },
    )


if __name__ == "__main__":
    # create_psycopg2_layer()
    main()
