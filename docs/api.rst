API
===

This part of the documentation covers all resources (routes) provided by
`senaite.jsonapi`_. It also covers all the request parameters that can be
applied to these resources to refine the results.


.. _Concept:

Concept
-------

The SENAITE JSON API aims to be **as fast as possible**. So the concept of the API
is to postpone **expensive operations** until the user really requests it. To do
so, the API was built with a **two step architecture**.

An **expensive operation** is basically given, when the API needs to "wake up"
an object to retrieve all its field values. This means the full object has to be
loaded from the Database (ZODB) into the memory (RAM).

The **two step architecture** retrieves only the fields of the catalog results
in the *first step*. Only if the user requests the API URL of a specific object,
the object will be loaded and all the fields of the object will be returned.

.. note:: You can add a `complete=yes` parameter to bypass the two step behavior
          and retrieve the full object data immediately.

.. _BASE_URL:

Base URL
--------

After installation, the SENAITE API routes are available below the
senaite.jsonapi root URL (``@@API``), with the base ``/senaite/api/v1``.

Example: ``http://localhost:8080/senaite/@@API/senaite/v1/version``

.. _Resources:

Resources
---------

:URL Schema: ``<BASE URL>/<RESOURCE>/<OPERATION>/<uid:optional>``

A resource is equivalent with the portal type name in SENAITE.

This means that all portal types are fully supported by the API simply by adding
the portal type to the end of the base url, e.g.:

    - http://localhost:8080/senaite/@@API/senaite/v1/Client
    - http://localhost:8080/senaite/@@API/senaite/v1/AnalysisService
    - http://localhost:8080/senaite/@@API/senaite/v1/AnalysisRequest

.. note:: Lower case portal type names are also supported.


.. _Operations:

Operations
----------

The API understands the basic `CRUD`_ operations on the *content resources*.
Only the READ operation is accessible via a HTTP GET request. All other
operations have to be sent via a HTTP POST request.

+-----------+---------------------------------------------+--------+
| OPERATION | URL                                         | METHOD |
+===========+=============================================+========+
| READ      | <BASE URL>/<RESOURCE>/<uid:optional>        | GET    |
+-----------+---------------------------------------------+--------+
| CREATE    | <BASE URL>/<RESOURCE>/create/<uid:optional> | POST   |
+-----------+---------------------------------------------+--------+
| UPDATE    | <BASE URL>/<RESOURCE>/update/<uid:optional> | POST   |
+-----------+---------------------------------------------+--------+
| DELETE    | <BASE URL>/<RESOURCE>/delete/<uid:optional> | POST   |
+-----------+---------------------------------------------+--------+

.. note:: For traceability reasons, *delete* operation is not supported in
          SENAITE LIMS. When *delete* operation is used, the system tries to
          deactivate the object instead.

It is also possible to get the contents by UID directly from the base url,
without the need of <RESOURCE>, e.g.:

    - http://localhost:8080/senaite/@@API/senaite/v1/<uid>

This principle not applies to VIEW operation only, but to UPDATE and
DELETE too. When the UID is directly used, <RESOURCE> becomes optional:

+-----------+---------------------------------------------+--------+
| OPERATION | URL                                         | METHOD |
+===========+=============================================+========+
| READ      | <BASE URL>/<RESOURCE:optional>/<uid>        | GET    |
+-----------+---------------------------------------------+--------+
| CREATE    | <BASE URL>/<RESOURCE:optional>/create/<uid> | POST   |
+-----------+---------------------------------------------+--------+
| UPDATE    | <BASE URL>/<RESOURCE:optional>/update/<uid> | POST   |
+-----------+---------------------------------------------+--------+
| DELETE    | <BASE URL>/<RESOURCE:optional>/delete/<uid> | POST   |
+-----------+---------------------------------------------+--------+

Therefore, the following urls are also valid:

    - http://localhost:8080/senaite/@@API/senaite/v1/create/<uid>
    - http://localhost:8080/senaite/@@API/senaite/v1/update/<uid>
    - http://localhost:8080/senaite/@@API/senaite/v1/delete/<uid>


.. _Users_Resource:

Users Resource
--------------

The API is capable to find SENAITE users, e.g.:

    - http://localhost:8080/senaite/@@API/senaite/v1/users
    - http://localhost:8080/senaite/@@API/senaite/v1/users/current
    - http://localhost:8080/senaite/@@API/senaite/v1/users/<username>

.. code-block:: javascript

    {
        count: 50,
        pagesize: 25,
        items: [
            {
                username: "jordi",
                visible_ids: false,
                linked_contact_uid: "e980f398c233488b96d733a49b73c8b8",
                authenticated: false,
                api_url: "http://localhost:8080/senaite/@@API/senaite/v1/users/jordi",
                roles: [
                    "Member",
                    "LabManager",
                    "Authenticated"
                ],
                home_page: "",
                description: "",
                wysiwyg_editor: "",
                location: "",
                error_log_update: 0,
                language: "",
                listed: true,
                groups: [
                    "AuthenticatedUsers",
                    "Clients",
                    "LabManagers",
                ],
                portal_skin: "",
                fullname: "Jordi Puiggené",
                login_time: "2000-01-01T00:00:00",
                email: "jp@naralabs.com",
                ext_editor: false,
                last_login_time: "2000-01-01T00:00:00"
            },
        ],
        page: 1,
        _runtime: 0.008383989334106445,
        next: "http://localhost:8080/senaite/@@API/senaite/v1/users?b_start=25",
        pages: 2,
        previous: null
    }

The results come as well as batches of 25 items per default. It is also possible
to get a higher or lower number of users per batch with the `?limit=n` request
parameter, e.g.:

    - http://localhost:8080/senaite/@@API/senaite/v1/users?limit=1

.. note:: This route lists all users for **authenticated** users only.

The username `current` is reserved to fetch the current logged in user:

    - http://localhost:8080/senaite/@@API/senaite/v1/users/current

Overview
~~~~~~~~

+----------+--------------------+----------------------------------------+
| Resource | Action             | Description                            |
+==========+====================+========================================+
| users    | <username>,current | Resource for SENAITE Users             |
+----------+--------------------+----------------------------------------+
| auth     |                    | Basic Authentication                   |
+----------+--------------------+----------------------------------------+
| login    |                    | Login with __ac_name and __ac_password |
+----------+--------------------+----------------------------------------+
| logout   |                    | De-authenticate                        |
+----------+--------------------+----------------------------------------+


.. _Catalogs_Resource:

Catalogs Resource
-----------------

`senaite.jsonapi` is capable to retrieve information about the catalogs
registered in the system, as well as the indexes and metadata fields (schema)
they contain:

    - http://localhost:8080/senaite/@@API/senaite/v1/catalogs
    - http://localhost:8080/senaite/@@API/senaite/v1/catalogs/<catalog_id>

For each catalog, the following information is provided:

    - `id`: the unique identifier of the catalog
    - `indexes`: the list of indexes the catalog contains (used for searches)
    - `schema`: the list of metadata fields the catalog contains
    - `portal_types`: types that are indexed in this catalog

Example:

    - http://localhost:8080/senaite/@@API/senaite/v1/catalogs/bika_catalog

.. code-block:: javascript

    {
        _runtime: 0.0061838626861572266,
        id: "bika_catalog",
        schema: [
            "Created",
            "Description",
            "Title",
            "Type",
            "UID",
            "creator",
            ...
        ],
        portal_types: [
            "Batch",
            "ReferenceSample",
        ],
        indexes: [
            "BatchDate",
            "Creator",
            "Description",
            "Title",
            "Type",
            "UID",
            ...
        ]
    }


.. note:: the `indexes` of a catalog can either be used as filters for
          searching results and as criteria for sorting the results.

.. note:: `schema` fields are the keys of the values `senaite.jsonapi` will
          display in a search query for a given resource and catalog in
          accordance with the *two step architecture* strategy explained in
          :ref:`Concept`.


.. _Search_Resource:

Search Resource
---------------

The search route omits the portal type and is therefore capable to search for
**any** content type within the portal that is indexed in `portal_type` catalog.

The search route accepts all available indexes which are defined in the portal
catalog tool, e.g.:

    - http://localhost:8080/senaite/@@API/senaite/v1/search

Returns **all** contents indexed in `portal_catalog`.

    - http://localhost:8080/senaite/@@API/senaite/v1/search?id=test

Returns contents that match with the given value of the `id` parameter.

By default, `Plone`_ objects are stored in a generalist catalog, named
`portal_catalog`. SENAITE LIMS is built on top of Plone and also makes use of
this generalist catalog, but **not all objects are stored in this catalog**.
Rather, SENAITE LIMS follows a multi-catalog approach given the heterogeneity of
object types it contains, with different requirements in terms of indexes for
searches. The immediate benefit is that system becomes more performant, but at
a cost: the user has to know the catalog to search against.

Searches by catalog
~~~~~~~~~~~~~~~~~~~

You can check the catalogs registered in the system and locate the portal type
you want to search with the route `catalogs`, as explained in :ref:`Catalogs_Resource`.

Not all catalogs have same indexes, so once you know the catalog to search against,
you might need to check the indexes it contains you are using a supported
parameter for your search.

The following is a catalog-specific search (note the param `catalog` in the url):

    - http://localhost:8080/senaite/@@API/senaite/v1/search?id=WB-00012&catalog=bika_catalog_analysisrequest_listing

Returns the contents indexed with id `WB-00012` in the specified catalog. This
catalog only contains objects from type `AnalysisRequest` (aka Sample), so we
expect this query to return a single item, a Sample:

.. code-block:: javascript

    {
        count: 1,
        pagesize: 25,
        items: [
            {
                getSampleTypeUID: "39cbccd290a64894853d9d28ad297d33",
                getProgress: 40,
                getDueDate: "2020-05-01T16:01:23+02:00",
                getBatchID: "",
                getContactFullName: "Rita Mohale",
                url: "http://localhost:8080/senaite/clients/client-1/WB-00012",
                path: "/senaite/senaite/clients/client-1/WB-00012",
                uid: "19697c28034a4d3a960540b938203b50",
                id: "WB-00012",
                getDateSampled: "2020-04-27T00:00:00+02:00",
                parent_id: "client-1",
                getInternalUse: false,
                api_url: "http://localhost:8080/senaite/@@API/senaite/v1/analysisrequest/19697c28034a4d3a960540b938203b50",
                getClientTitle: "Happy Hills",
                portal_type: "AnalysisRequest",
                ...
            }
        ],
        page: 1,
        _runtime: 9.699778079986572,
        next: null,
        pages: 1,
        previous: null
    }

.. note:: Remember that `senaite.jsonapi` follows a **two-step strategy** on
          searches, so only the catalog metadata of the item is displayed unless
          you add the parameter `&complete=True` in the URL.

Searches by index
~~~~~~~~~~~~~~~~~

Search of resources supports the use of indexes as filter criteria. Note that
we've used the param `id` in the above mentioned searches. In fact, `id` is an
index that is present either in default `portal_catalog` and in the catalog for
which we've done the catalog-specific search.

Remember you can check the indexes available for any given catalog by using the
:ref:`Catalogs route`. For instance:

    - http://localhost:8080/senaite/@@API/senaite/v1/search?portal_type=Client

Will return all the objects their value for `portal_type` index is `Client` and
that are stored in the default catalog `portal_catalog`. Obviously, this url
returns exactly the same result as if we were using the route `client`:

    - http://localhost:8080/senaite/@@API/senaite/v1/client

But `portal_catalog` has other indexes that might be of our interest for
searches:

    - http://localhost:8080/senaite/@@API/senaite/v1/search?review_state=inactive

Will return the items, regardless of the type, that are stored in `portal_catalog`
that are in inactive status.

Searches by index can also be used against other catalogs:

    - http://localhost:8080/senaite/@@API/senaite/v1/search?getClientID=HHILLS&bika_catalog_analysisrequest_listing

Will return all the samples assigned to client with id `HHILLS`. Note this is
not the internal ID of the client object, rather the id assigned manually by
user on Client creation.

We can also combine multiple indexes in our search:

    - http://localhost:8080/senaite/@@API/senaite/v1/search?getClientID=HHILLS&review_state=published&catalog=bika_catalog_analysisrequest_listing

Will return the samples assigned to client with id `HHILLS` their status is
`published`.


Sorting and limiting results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Results can also be sorted by any index present in the catalog, by using the
`sort_on` parameter:

    - http://localhost:8080/senaite/@@API/senaite/v1/search?getClientID=HHILLS&review_state=published&sort_on=getDateSampled&catalog=bika_catalog_analysisrequest_listing

Will return the samples assigned to client with id `HHILLS` their status is
`published`, sorted by date sampled ascending. We can also sort the results
descending with parameter `sort_order`:

    - http://localhost:8080/senaite/@@API/senaite/v1/search?getClientID=HHILLS&review_state=published&sort_on=getDateSampled&sort_order=desc&catalog=bika_catalog_analysisrequest_listing

In addition to sorting, we can also limit the number of results to a given
number:

    - http://localhost:8080/senaite/@@API/senaite/v1/search?getClientID=HHILLS&review_state=published&sort_on=getDateSampled&sort_order=desc&limit=10&catalog=bika_catalog_analysisrequest_listing

Will return the first 10 samples that are assigned to a client with id `HHILLS`,
their status is `published`, sorted by date sampled descending.

.. _Parameters:

Parameters
----------

:URL Schema: ``<BASE URL>/<RESOURCE>?<KEY>=<VALUE>&<KEY>=<VALUE>``

All content resources accept to be filtered by request parameters.

+-----------------+-----------------------+-------------------------------------------------------------------------+
| Key             | Value                 | Description                                                             |
+=================+=======================+=========================================================================+
| q               | searchterm            | Search the SearchableText index for the given query string              |
+-----------------+-----------------------+-------------------------------------------------------------------------+
| path            | /physical/path        | Specifiy a physical path to only return results below it.               |
|                 |                       | See how to `Query by path`_ in the `Plone docs`_ for details.           |
+-----------------+-----------------------+-------------------------------------------------------------------------+
| depth           | 0..n                  | Specify the depth of a path query. Only relevant when using             |
|                 |                       | the path parameter.                                                     |
+-----------------+-----------------------+-------------------------------------------------------------------------+
| catalog         | catalog name          | Search for results against the specified catalog                        |
+-----------------+-----------------------+-------------------------------------------------------------------------+
| limit           | 1..n                  | Limit the results to the given `limit` number.                          |
|                 |                       | This will return batched results with `x` pages and `n` items per page  |
+-----------------+-----------------------+-------------------------------------------------------------------------+
| sort_on         | catalog index         | Sort the results by the given index                                     |
+-----------------+-----------------------+-------------------------------------------------------------------------+
| sort_order      | asc / desc            | Sort ascending or descending (default: ascending)                       |
+-----------------+-----------------------+-------------------------------------------------------------------------+
| sort_limit      | 1..n                  | Limit the result set to n items.                                        |
|                 |                       | The portal catalog will only return n items.                            |
+-----------------+-----------------------+-------------------------------------------------------------------------+
| complete        | yes/y/1/True          | Flag to return the full object results immediately.                     |
|                 |                       | Bypasses the *two step* behavior of the API                             |
+-----------------+-----------------------+-------------------------------------------------------------------------+
| children        | yes/y/1/True          | Flag to return the folder contents of a folder below the `children` key |
|                 |                       | Only visible if complete flag is true or if an UID is provided          |
+-----------------+-----------------------+-------------------------------------------------------------------------+
| workflow        | yes/y/1/True          | Flag to include the workflow data below the `workflow` key              |
+-----------------+-----------------------+-------------------------------------------------------------------------+
| filedata        | yes/y/1/True          | Flag to include the base64 encoded file                                 |
+-----------------+-----------------------+-------------------------------------------------------------------------+
| recent_created  | today, yesterday      | Specify a recent created date range, to find all items created within   |
|                 | this-week, this-month | this date range until today.                                            |
|                 | this-year             | This uses internally `'range': 'min'` query.                            |
+-----------------+-----------------------+-------------------------------------------------------------------------+
| recent_modified | today, yesterday      | Specify a recent modified date range, to find all items modified within |
|                 | this-week, this-month | this date range until today.                                            |
|                 | this-year             | This uses internally `'range': 'min'` query.                            |
+-----------------+-----------------------+-------------------------------------------------------------------------+

.. _Response_Format:

Response Format
---------------

The response format is for all resources the same.

.. code-block:: javascript

    {
        count: 1, // number of found items
        pagesize: 25, // items per page
        items: [  // List of all item objexts
            {
                id: "front-page", // item data
                ...
            }
        ],
        page: 1, // current page
        _runtime: 0.00381,  // calculation time to generate the data
        next: null,  // URL to the next batch
        pages: 1,  //  number of total pages
        previous: null  // URL to the previous batch
    }


**count**
    The number of found items -- can be more than displayed on one site

**pagesize**
    Number of items per page

**items**
    List of found items -- only catalog brain keys unless you add a
    `complete=yes` parameter to the request or request an URL with an UID at
    the end.

**page**
    The current page of the batched result set

**_runtime**
    The time in milliseconds needed to generate the data

**next**
    The URL to the next batch

**pages**
    The number of pages in the batch

**previous**
    The URL to the previous batch

.. Links

.. _Plone: http://plone.org
.. _Plone docs: http://docs.plone.org/develop/plone/searching_and_indexing/query.html#query-by-path
.. _Query by path: http://docs.plone.org/develop/plone/searching_and_indexing/query.html#query-by-path
.. _CRUD: http://en.wikipedia.org/wiki/CRUD
.. _catalog module from senaite.core: https://github.com/senaite/senaite.core/tree/master/bika/lims/catalog
.. _senaite.jsonapi: https://github.com/senaite/senaite.jsonapi
