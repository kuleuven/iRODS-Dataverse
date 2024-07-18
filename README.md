# iRODS-Dataverse
This is an implementation for programmatic publication of data from iRODS into a Dataverse installation.

## Prerequisites 
1) Being an iRODS user with data in an iRODS zone.
2) Authenticate to Dataverse:
- Sign up with individual account
- Get the API Token which is valid for a certain amount of time (demo: one year)
3) Run the scripts with internet access


## Set up the virtual environment
```
$ python -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

When finished, deactivate the virtual environment
```
$ deactivate
```

## User script
After the virtual environment is activated run:
```
$ python src/userScript.py
```
