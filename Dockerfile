FROM amazonlinux:latest
RUN yum -y install python27 python27-devel python27-pip zip unzip && yum -y groupinstall "Development tools" && pip install --upgrade pip && pip install virtualenv && yum clean all
ADD create_lamdba_package.sh /
ENTRYPOINT ["/bin/bash","/create_lamdba_package.sh"]