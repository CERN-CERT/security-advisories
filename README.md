# Advisories

A simple service providing Markdown document sharing with contacts. 

## Features
* New URL generation per contact for each shared document to prevent leaking.
* Access tracking per document (contact URL, IP and browser) 

## Deployment

### Configuration
create a `.env` file with the following variables. Replace the default passwords/keys with something more secure. 

```
### postgresdb vars
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=some-db-password

### app vars
DB_URL=postgresql://postgres:some-password@db:5432/postgres
SECRET_KEY=some-secret-key
#SERVER_NAME=
```

### Setup
As this is a Flask application, there are many popular deployment options for serving `advisories`. At the moment, the proposed WSGI container is using docker compose.

Build the app image
```
docker compose build --no-cache
```

Run the app 
```shell
docker compose up -d
```

By default, `3` processes and `1` thread are used for `Gunicorn`. Those values can be altered by setting the environment variables below:

* `GUNICORN_PROCESSES`
* `GUNICORN_THREADS`

## Usage

There are only two operations:

### Creating / editing an advisory

This is done on the `/admin/` page via the `Upload new post` area, simply by entering a plain-text title and a Markdown-formatted text blob.
Once the text is submitted, the advisory will be listed in the `Current posts` part on the same page.

For each advisory, content can be managed by clicking on the advisory title or number, from the `/admin/` page.
This allows to:
- Edit the plain-text title and a Markdown-formatted text of the advisory
- Delete the advisory
 
### Sharing unique links for an advisory

Creating unique links (one per recipient) is done on the `/admin/` page, by entering a label for the recipients name in the `Link for` field, and clicking `add`.

The unique link to be shared with the newly created recipient is available by clicking on the advisory title or number, from the `/admin/` page.

For each advisory, possible sharing rules violations can also be managed by clicking on the advisory title or number, from the `/admin/` page.
This allows to:
* View the URL to be shared for each recipient
* Delete unique sharing links
* Monitor the unique URL browsing patterns (`Datetime`, `IP`, `Referrer`)

## License
This software is distributed under the terms of the MIT Licence, copied verbatim in the file 'LICENSE'. In applying this licence, CERN does not waive the privileges and immunities granted to it by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
