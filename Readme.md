How to use:

On line 8 change the Elastic serch URL

```
$ mkdir lambda
$ cd lambda 
$ pip3 install requests -t .
$ pip3 install boto3 -t . 
$ pip3 install regex -t .

Zip the library to use in lambda 

$ zip -r lambda.zip *

```
Create a lambda with ython 3.8 as a runtime use the Zip file as a source code.

Handler : s3-lambda-es_handler

Trigger:

1. Add the trigger to lambda with S3
2. Upload the log file to S3 to a specifc trigger folder 
3. View the logs on Kibana
