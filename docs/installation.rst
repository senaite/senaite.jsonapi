Installation
============

To install senaite.jsonapi in your SENAITE instance, simply add this add-on
in your buildout configuration file as follows, and run `bin/buildout`
afterwards:

.. code-block:: ini

    [buildout]

    ...

    [instance]
    ...
    eggs =
        ...
        senaite.jsonapi


With this configuration, buildout will download and install the latest published
release of `senaite.jsonapi from Pypi`_.

The routes for SENAITE LIMS content types get registered on startup. The
following URL should be available after startup:

http://localhost:8080/senaite/@@API/senaite/v1


JSON Viewers and REST clients
-----------------------------

There are plenty of add-ons for browsers that beautify the generated JSON,
making it's interpretation more comfortable for humans. Below, some plugins you
can install in your browser:

- `JSONView for Firefox`_
- `JSON Lite for Firefox`_
- `JSONView for Google Chrome`_

Below, some applications to send POST requests to senaite.jsonapi:

- `RESTClient for Firefox`_
- `Advanced REST Client for Google Chrome`_


.. Links

.. _senaite.jsonapi from Pypi: https://pypi.org/project/senaite.jsonapi
.. _JSONView for Firefox: https://addons.mozilla.org/de/firefox/addon/jsonview
.. _JSON Lite for Firefox: https://addons.mozilla.org/en-US/firefox/addon/json-lite
.. _JSONView for Google Chrome: https://chrome.google.com/webstore/detail/jsonview/chklaanhfefbnpoihckbnefhakgolnmc?hl=en
.. _RESTClient for Firefox: https://addons.mozilla.org/en-US/firefox/addon/restclient/
.. _Advanced REST Client for Google Chrome: https://chrome.google.com/webstore/detail/advanced-rest-client/hgmloofddffdnphfgcellkdfbfbjeloo