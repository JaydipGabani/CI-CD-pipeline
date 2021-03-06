import boto3
import sys
import logging
import os


def get_session(region, access_id, secret_key):
    return boto3.session.Session(region_name=region, aws_access_key_id=access_id, aws_secret_access_key=secret_key)

session = get_session(os.getenv('AWS_REGION'), os.getenv('AWS_ACCESS_KEY_ID'), os.getenv('AWS_SECRET_ACCESS_KEY'))
ec2 = session.resource('ec2')
ec2_client = session.client('ec2')


def write_ini(inst):
    keypair = "/home/vagrant/.ssh/ec2-KP-devops06"
    with open('/home/vagrant/deploy.ini', 'w+') as outfile:
        for iname, iip in inst.items():
            outfile.write("[{}]\n".format(iname))
            outfile.write("{} ansible_ssh_private_key_file={} ansible_user={}\n".format(iip, keypair, "ubuntu"))
            #outfile.write("[{}]\n".format(iname+":"+"vars"))
            #outfile.write("ansible_ssh_common_args={}\n".format('-o StrictHostKeyChecking=no'))


def get_instances():

    inst = {}
    names = ['checkbox', 'itrust', 'monitor']
    # get all the running resources
    instances = ec2.instances.filter(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])

    for instance in instances:
        ec2instance = ec2.Instance(instance.id)
        for tags in ec2instance.tags:
            if tags['Key'] == 'Name':
                ans = ec2_client.describe_instances(InstanceIds=[instance.id])
                if tags['Value'] in names:
                    inst[tags['Value']] = ans['Reservations'][0]['Instances'][0]['PublicIpAddress']
    return inst


def create_instance(inst):

    resp = ec2.create_instances(ImageId='ami-04b9e92b5572fa0d1', MinCount=1, MaxCount=1, InstanceType='t2.micro', KeyName='ec2-KP-devops06')
    print(resp)
    resp = resp[0]
    resp.wait_until_running()
    resp.load()
    rsrc_id = str(resp.instance_id)

    ec2.create_tags(Resources=[rsrc_id], Tags=[{'Key': 'Name', 'Value': inst}])

    ans = ec2_client.describe_instances(InstanceIds=[rsrc_id])

    iip = ans['Reservations'][0]['Instances'][0]['PublicIpAddress']
    return iip

if __name__ == "__main__":
    # get checkbox.io, iTrust, monitoring VMs IPs if present
    instances = get_instances()
    names = ['checkbox', 'itrust', 'monitor']
    create_inst = []
    for i in names:
        if i in instances:
            continue
        else:
            create_inst.append(i)

    # create instance
    for i in create_inst:
        instances[i] = create_instance(i)

    # write IP of monitor vm in ip.txt
    with open ('/home/vagrant/monitor_ip.txt', 'w+') as ipfile:
        ipfile.write(instances['monitor'])

    # write IP of checkbox vm in ip.txt
    with open ('/home/vagrant/checkbox_ip.txt', 'w+') as ipfile:
        ipfile.write(instances['checkbox'])
    
    # write IP of itrust vm in ip.txt
    with open ('/home/vagrant/itrust_ip.txt', 'w+') as ipfile:
        ipfile.write(instances['itrust'])

    # security group
    try:
        ec2_client.authorize_security_group_ingress(
            GroupId='sg-0a29706d9a6e61063',
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 0,
                    'ToPort': 65535,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }
            ]
        )
    except:
        logging.info("Security group configuration already exists")            

    # write instances IP in the .ini file
    write_ini(instances)
