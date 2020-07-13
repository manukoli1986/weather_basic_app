# Using Base image alpine with installed python3
FROM frolvlad/alpine-python3

MAINTAINER "Mayank Koli"

#choosing /usr/src/app as working directory
WORKDIR /usr/src/app

# Mentioned python module name to run application 

COPY . ./
RUN pip3 install --no-cache-dir -r requirements.txt

# Exposing applicaiton on 80 so that it can be accessible on 80
EXPOSE 8080

#Copying code to working directory
COPY . .

#Making default entry as python will launch api.py
CMD [ "python3", "app.py" ]
