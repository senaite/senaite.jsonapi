Quickstart
==========

This section gives an introduction about `senaite.jsonapi`_. It assumes you
have `SENAITE LIMS`_ and `senaite.jsonapi` already installed. The JSON API is
therefore located at `http://localhost:8080/senaite/@@API/senaite/v1`. Make
sure your SENAITE LIMS instance is located on the same URL, so you can directly
click on the links within the examples.

All the coming examples are executed directly in Google Chrome. `JSONView_`
is used to beautify the generated JSON and the `Advanced Rest Client`_ Application
to send POST requests to `senaite.jsonapi`_. See :doc:`installation` for details.


Version route
-------------

The `version` route prints out the current version of `senaite.jsonapi`.

http://localhost:8080/senaite/@@API/senaite/v1/version

.. code-block:: javascript

    {
        url: "http://localhost:8080/senaite/@@API/senaite/v1/version",
        date: "2020-03-03",
        version: "1.2.2",
        _runtime: 0.0036830902099609375
    }

.. note:: The runtime indicates the time spent in milliseconds until the
          response is prepared.

Content Routes
--------------

`senaite.jsonapi` allows you to directly retrieve contents by their `portal_type`
name. These :ref:`Resources` are automatically generated for **all** available
content types in SENAITE.

Each content route is located at the :ref:`BASE_URL`, e.g.

  - http://localhost:8080/senaite/@@API/senaite/v1/client
  - http://localhost:8080/senaite/@@API/senaite/v1/analysisrequest

The name of each of these content routes is transformed to lower case, so it is
also perfectly ok to call these :ref:`Resources` like so:

  - http://localhost:8080/senaite/@@API/senaite/v1/Client
  - http://localhost:8080/senaite/@@API/senaite/v1/AnalysisRequest

For instance, calling a content route like

  - http://localhost:8080/senaite/@@API/senaite/v1/client

will return a JSON containing records of type `Client` only:

.. code-block:: javascript

    {
        count: 1596,
        pagesize: 25,
        items: [
            {
                uid: "ffce0bba48204c63a62b0744a6b762bf",
                id: "client1",
                ...
                portal_type: "Client",
                ...
            },
            {},
            {},
            ...
        ],
        page: 1,
        _runtime: 0.09960794448852539,
        next: "http://localhost:8080/senaite/@@API/senaite/v1/client?b_start=25",
        pages: 64,
        previous: null
    }


Some examples of searches for SENAITE-specific portal types below:

- Analysis Services: http://localhost:8080/senaite/@@API/senaite/v1/analysisservice
- Calculations: http://localhost:8080/senaite/@@API/senaite/v1/calculation
- Samples: http://localhost:8080/senaite/@@API/senaite/v1/analysisrequest
- Worksheets: http://localhost:8080/senaite/@@API/senaite/v1/worksheet

Check out `senaite.core's types.xml`_ for the full list of portal types that
come with SENAITE LIMS by default. Keep in mind that `senaite.jsonapi` will also
handle other portal types that might be registered by other add-ons. For
instance, `SENAITE Health, an extension for health-care labs`_ registers a new
portal type named `Patient`. If you have this add-on installed, the url
http://locahost:8080/senaite/@@API/senaite/v1/patient will work as well,
returning the list of objects from type `Patient`.

From the JSON response above, note the following:

The :ref:`Response_Format` in `senaite.jsonapi` content URLs is always the
same. The top level keys (data after the first ``{``) are meta information
about the gathered data.

The `items` list will contain the list of results. Each result is a record
with just the metadata available in the catalog. Therefore, no object is
"waked up" at this stage. This is because of the APIs two step concept,
which postpones expensive operations, until the user really wants it.

All `items` are batched to increase performance of the API. The `count` number
returns the total number objects found, while the `page` number returns the
number of pages in the batch, which can be navigated with the `next` and
`previous` links.

Get records full data
~~~~~~~~~~~~~~~~~~~~~

To get all data from an object, you can either add the ``complete=True``
parameter, or you can request the data with the object ``UID``.

  - http://localhost:8080/senaite/@@API/senaite/v1/client?complete=True
  - http://localhost:8080/senaite/@@API/senaite/v1/client/<uid>
  - http://localhost:8080/senaite/@@API/senaite/v1/<uid>

The requested content(s) is now loaded by the API and all fields are gathered.

.. note:: Please keep in mind that large data sets with the `?complete=True`
          Parameter might increase the loading time significantly.

UID Route
---------

To fetch the full data of an object immediately, it is also possible to append
the UID of the object directly on the root URL of the API, e.g.:

    - http://localhost:8080/senaite/@@API/senaite/v1/ffce0bba48204c63a62b0744a6b762bf
    - http://localhost:8080/senaite/@@API/senaite/v1/client/ffce0bba48204c63a62b0744a6b762bf

.. note:: The given UID might seem different on your machine.

The response will give the data in the root of the JSON data, so only the
object metadata is returned, e.g.:

.. code-block:: javascript

    {
        expirationDate: "2019-05-02T11:53:13+02:00",
        _runtime: 0.03150486946105957,
        exclude_from_nav: null,
        BankBranch: null,
        Fax: null,
        title: "Happy Hills",
        parent_id: "clients",
        location: null,
        parent_url: "http://localhost:8080/senaite/@@API/senaite/v1/clientfolder/b7e8d2288af74092afe0cf3a0e172f87",
        PhysicalAddress: {
            city: "Barcelona",
            district: "",
            zip: "",
            country: "Spain",
            state: "Catalonia",
            address: ""
        },
        portal_type: "Client",
        AccountName: null,
        language: "en",
        BulkDiscount: null,
        parent_uid: "b7e8d2288af74092afe0cf3a0e172f87",
        parent_path: "/senaite/clients",
        rights: null,
        AccountNumber: null,
        modified: "2019-07-24T23:14:57+02:00",
        EmailAddress: null,
        BillingAddress: {
            city: "",
            district: "",
            zip: "",
            country: "",
            state: "",
            address: ""
        },
        ...
    }

.. Links

.. _senaite.jsonapi: https://pypi.python.org/pypi/senaite.jsonapi
.. _SENAITE LIMS: https://www.senaite.com
.. _senaite.core's types.xml: https://github.com/senaite/senaite.core/tree/master/bika/lims/profiles/default/types
.. _SENAITE Health, an extension for health-care labs: https://pypi.org/project/senaite.health
.. _Advanced Rest Client: https://chrome.google.com/webstore/detail/advanced-rest-client/hgmloofddffdnphfgcellkdfbfbjeloo
.. _JSONView: https://chrome.google.com/webstore/detail/jsonview
