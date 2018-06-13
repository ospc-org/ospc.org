Jenkins Documentation
=====================

First define the Jenkins IP address, an AWS IP address you can get from Matt Jensen (matt.jensen [at] aei [dot] org).  Then define an environment variable so you can `scp` (secure copy) the `jenkins.zip` to your laptop (this is a temporary step until there is a more permanent storage solution for `jenkins.zip` - 2GB).

```bash
export JENKINS_IP=1.2.3.4
scp -i latest.pem ec2-user@${JENKINS_IP}:/var/lib/jenkins.zip ./jenkins.zip

```

Use `scp` to copy the zip to a new machine from which you want to run a Jenkins service, e.g. copying from the local directory to a remote IP at `/var/lib`:

```bash
export JENKINS_IP=1.2.3.4
scp -i latest.pem ./jenkins.zip ec2-user@${JENKINS_IP}:/var/lib/jenkins.zip

```

Next `ssh` into the `JENKINS_IP` AWS instance and unzip the `jenkins.zip`:
```bash
export JENKINS_IP=1.2.3.4
ssh -i latest.pem ec2-user@${JENKINS_IP}
cd /var/lib
unzip jenkins.zip
```

The following command will start the main Jenkins process:

```bash
/etc/alternatives/java -Djava.awt.headless=true -DJENKINS_HOME=/var/lib/jenkins -jar /usr/lib/jenkins/jenkins.war --logfile=/var/log/jenkins/jenkins.log --webroot=/var/cache/jenkins/war --httpPort=8080 --debug=5 --handlerCountMax=100 --handlerCountMaxIdle=20
```

Navigate to the Jenkins IP address in your browser:

```
1.2.3.4:8080
```

and confirm you can see the Jenkins UI.  Check with Matt Jensen if you are unsure about credentials from here.  Once authenticated, you should be able to find the policybrain-builder job (and earlier OG-USA regression testing harnesses are also in the saved Jenkins configuration, but these would require adaptation to OG-USA of recent 6 to 8 months)

Troubleshooting
---------------
Jenkins has several encrypted passwords or tokens. If you encounter package building problems, here are some things to check:

 * First make sure Jenkins encrypted passwords are up to date. You'll want to check its tokens for uploading to the `ospc` channel on `anaconda.org
<http://anaconda.org>`_
 as well as the token for the `ospctaxbrain`, both of which have expirations approximately every 6 to 12 months (see the options with `anaconda auth --help` if making new tokens).
 * Next check `Policybrain-builder
<https://github.com/open-source-economics/policybrain-builder/>`_ for open issues that may relate to your problem
 * You may also want to see this `Conda Packaging Tutorial<https://docs.google.com/presentation/d/1ohGxdJT6B0v_HaGTOMRZzP8g7bynfTzqYm1IeK3V9W8/edit#slide=id.g23d4eefcd7_0_11>`_ or `this Running Policybrain-builder to build TaxBrain Packages<https://docs.google.com/presentation/d/1S2GfFF7-21wfUgu0LNFxcKuGNxcHAG_hdZBDZx79UKg/edit#slide=id.p>`_ tutorial.  Note that some of the material in those linked slidedecks is no longer up-to-date with respect to current release processes, e.g. the info on tagging in Github, but they are a good overview of `conda` and Jenkins.
 * If you are doing this on a new AWS box and you can't access the Jenkins worker in your browser, then check your AWS security group settings to see that port `8080` is open to your laptop's access.

